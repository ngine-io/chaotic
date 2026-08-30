"""Tests for the Nomad API client and the two Nomad experiments."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests
import responses

from chaotic.errors import ConfigError
from chaotic.providers.nomad import DEFAULT_NOMAD_ADDR, NANOSECONDS_PER_SECOND, Nomad, NomadChaotic
from tests.conftest import make_provider, recorded_request_kwargs

ADDR = "http://nomad.example.com:4646"


def alloc(name: str, **overrides: Any) -> dict[str, Any]:
    return {
        "ID": f"id-{name}",
        "Name": name,
        "NodeName": "node-1",
        "ClientStatus": "running",
        "JobID": name,
        "JobType": "service",
        **overrides,
    }


def node(name: str, **overrides: Any) -> dict[str, Any]:
    return {
        "ID": f"id-{name}",
        "Name": name,
        "NodeClass": "compute",
        "Drain": False,
        "SchedulingEligibility": "eligible",
        **overrides,
    }


# --------------------------------------------------------------------------- #
# API client
# --------------------------------------------------------------------------- #
@pytest.fixture
def api() -> Nomad:
    return Nomad(api_key="nomad-token", api_url=ADDR)


def test_client_defaults_to_localhost() -> None:
    assert Nomad(api_key="").api_url == DEFAULT_NOMAD_ADDR
    assert Nomad(api_key="", api_url="").api_url == DEFAULT_NOMAD_ADDR


def test_client_parses_http_auth() -> None:
    assert Nomad(api_key="", api_auth="user:pass").api_auth == ("user", "pass")
    assert Nomad(api_key="", api_auth="").api_auth is None


@responses.activate
def test_requests_carry_token_and_timeout(api: Nomad) -> None:
    responses.get(f"{ADDR}/v1/nodes", json=[])
    api.list_nodes()

    request = responses.calls[0].request
    assert request.headers["X-Nomad-Token"] == "nomad-token"
    assert recorded_request_kwargs(responses.calls[0])["timeout"] == 10


@responses.activate
def test_list_nodes_filters_draining_and_ineligible(api: Nomad) -> None:
    responses.get(
        f"{ADDR}/v1/nodes",
        json=[
            node("ok"),
            node("draining", Drain=True),
            node("ineligible", SchedulingEligibility="ineligible"),
        ],
    )

    assert [n["Name"] for n in api.list_nodes()] == ["ok"]


@responses.activate
def test_drain_node_sends_a_nanosecond_deadline(api: Nomad) -> None:
    responses.post(f"{ADDR}/v1/node/id-1/drain", json={})
    api.drain_node("id-1", deadline_seconds=15, ignore_system_jobs=False)

    body = json.loads(responses.calls[0].request.body or b"")
    assert body["DrainSpec"]["Deadline"] == 15 * NANOSECONDS_PER_SECOND
    assert body["DrainSpec"]["IgnoreSystemJobs"] is False
    assert body["Meta"] == {"message": "drained by chaotic"}


@responses.activate
@pytest.mark.parametrize(("eligible", "expected"), [(True, "eligible"), (False, "ineligible")])
def test_set_node_eligibility(api: Nomad, eligible: bool, expected: str) -> None:
    responses.post(f"{ADDR}/v1/node/id-1/eligibility", json={})
    api.set_node_eligibility("id-1", eligible=eligible)

    assert json.loads(responses.calls[0].request.body or b"") == {"Eligibility": expected}


@responses.activate
def test_list_allocs_passes_the_namespace(api: Nomad) -> None:
    responses.get(f"{ADDR}/v1/allocations", json=[alloc("web")])
    assert api.list_allocs(namespace="prod") == [alloc("web")]
    assert "namespace=prod" in str(responses.calls[0].request.url)


@responses.activate
def test_read_alloc(api: Nomad) -> None:
    responses.get(f"{ADDR}/v1/allocation/id-1", json={"ID": "id-1"})
    assert api.read_alloc("id-1") == {"ID": "id-1"}


@responses.activate
def test_signal_alloc(api: Nomad) -> None:
    responses.post(f"{ADDR}/v1/client/allocation/id-1/signal", json={})
    api.signal_alloc("id-1", "SIGKILL")
    assert json.loads(responses.calls[0].request.body or b"") == {"Signal": "SIGKILL"}


@responses.activate
def test_list_namespaces_passes_the_prefix(api: Nomad) -> None:
    responses.get(f"{ADDR}/v1/namespaces", json=[{"Name": "default"}])
    assert api.list_namespaces(prefix="def") == [{"Name": "default"}]
    assert "prefix=def" in str(responses.calls[0].request.url)


@responses.activate
def test_api_errors_are_raised(api: Nomad) -> None:
    responses.get(f"{ADDR}/v1/nodes", status=403)
    with pytest.raises(requests.HTTPError):
        api.list_nodes()


def test_provider_client_reads_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOMAD_ADDR", ADDR)
    monkeypatch.setenv("NOMAD_TOKEN", "tok")
    monkeypatch.setenv("NOMAD_HTTP_AUTH", "u:p")

    client = NomadChaotic().client
    assert (client.api_url, client.api_key, client.api_auth) == (ADDR, "tok", ("u", "p"))


# --------------------------------------------------------------------------- #
# Experiment dispatch
# --------------------------------------------------------------------------- #
def test_action_defaults_to_the_job_experiment(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider(NomadChaotic, MagicMock(), signals=["SIGKILL"])
    monkeypatch.setattr(provider, "action_job", MagicMock())

    provider.action()

    provider.action_job.assert_called_once_with()


def test_action_dispatches_the_node_experiment(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider(NomadChaotic, MagicMock(), experiments=["node"])
    monkeypatch.setattr(provider, "action_node", MagicMock())

    provider.action()

    provider.action_node.assert_called_once_with()


def test_action_rejects_unknown_experiments() -> None:
    provider = make_provider(NomadChaotic, MagicMock(), experiments=["job", "reboot-the-datacenter"])
    with pytest.raises(ConfigError, match="Unknown nomad experiments"):
        provider.action()


# --------------------------------------------------------------------------- #
# Job experiment
# --------------------------------------------------------------------------- #
def job_client(
    namespaces: list[str], allocs: list[dict[str, Any]], job_meta: dict[str, Any] | None = None
) -> MagicMock:
    client = MagicMock()
    client.list_namespaces.return_value = [{"Name": name} for name in namespaces]
    client.list_allocs.return_value = allocs
    client.read_alloc.return_value = {"Job": {"Meta": job_meta}}
    return client


def test_job_signals_a_running_alloc() -> None:
    client = job_client(["prod"], [alloc("web")])
    provider = make_provider(NomadChaotic, client, signals=["SIGKILL"])

    provider.action_job()

    client.list_allocs.assert_called_once_with(namespace="prod")
    client.signal_alloc.assert_called_once_with(alloc_id="id-web", signal="SIGKILL")


def test_job_requires_signals() -> None:
    provider = make_provider(NomadChaotic, job_client(["prod"], [alloc("web")]))
    with pytest.raises(ConfigError, match="requires a non-empty 'signals' config"):
        provider.action_job()


def test_job_dry_run_does_not_signal(caplog: pytest.LogCaptureFixture) -> None:
    client = job_client(["prod"], [alloc("web")])
    provider = NomadChaotic()
    provider.__dict__["client"] = client
    provider.configure(configs={"signals": ["SIGKILL"]}, dry_run=True)

    provider.action_job()

    client.signal_alloc.assert_not_called()
    assert "Selected signal: SIGKILL" in caplog.text


def test_job_skips_non_running_allocs(caplog: pytest.LogCaptureFixture) -> None:
    client = job_client(["prod"], [alloc("dead", ClientStatus="complete")])
    make_provider(NomadChaotic, client, signals=["SIGKILL"]).action_job()

    client.signal_alloc.assert_not_called()
    assert "No allocs found" in caplog.text


def test_job_type_skiplist() -> None:
    client = job_client(["prod"], [alloc("batch-job", JobType="batch"), alloc("web")])
    provider = make_provider(NomadChaotic, client, signals=["SIGKILL"], job_type_skiplist=["batch"])

    provider.action_job()

    client.signal_alloc.assert_called_once_with(alloc_id="id-web", signal="SIGKILL")


def test_job_skiplist() -> None:
    client = job_client(["prod"], [alloc("critical"), alloc("web")])
    provider = make_provider(NomadChaotic, client, signals=["SIGKILL"], job_skiplist=["critical"])

    provider.action_job()

    client.signal_alloc.assert_called_once_with(alloc_id="id-web", signal="SIGKILL")


def test_namespace_allowlist() -> None:
    client = job_client(["default", "prod"], [alloc("web")])
    provider = make_provider(NomadChaotic, client, signals=["SIGKILL"], namespace_allowlist=["prod"])

    assert provider.get_namespace() == "prod"


def test_namespace_denylist() -> None:
    client = job_client(["default", "prod"], [alloc("web")])
    provider = make_provider(NomadChaotic, client, signals=["SIGKILL"], namespace_denylist=["default"])

    assert provider.get_namespace() == "prod"


def test_no_eligible_namespace_stops_the_run(caplog: pytest.LogCaptureFixture) -> None:
    client = job_client(["default"], [alloc("web")])
    provider = make_provider(NomadChaotic, client, signals=["SIGKILL"], namespace_denylist=["default"])

    provider.action_job()

    client.list_allocs.assert_not_called()
    assert "No namespaces eligible" in caplog.text


@pytest.mark.parametrize(("meta", "expected"), [({"chaotic": "false"}, True), ({"chaotic": False}, True)])
def test_opt_out_is_honoured(meta: dict[str, Any], expected: bool, caplog: pytest.LogCaptureFixture) -> None:
    client = job_client(["prod"], [alloc("web")], job_meta=meta)
    provider = make_provider(NomadChaotic, client, signals=["SIGKILL"], job_meta_opt_key="chaotic")

    provider.action_job()

    client.signal_alloc.assert_not_called()
    assert "opt-out configured" in caplog.text


@pytest.mark.parametrize("meta", [{"chaotic": "true"}, {"other": "false"}, {}, None])
def test_opt_in_and_missing_meta_allow_chaos(meta: dict[str, Any] | None) -> None:
    client = job_client(["prod"], [alloc("web")], job_meta=meta)
    provider = make_provider(NomadChaotic, client, signals=["SIGKILL"], job_meta_opt_key="chaotic")

    provider.action_job()

    client.signal_alloc.assert_called_once()


def test_opt_out_key_unset_skips_the_extra_api_call() -> None:
    client = job_client(["prod"], [alloc("web")])
    provider = make_provider(NomadChaotic, client, signals=["SIGKILL"])

    provider.action_job()

    client.read_alloc.assert_not_called()


# --------------------------------------------------------------------------- #
# Node experiment
# --------------------------------------------------------------------------- #
def node_client(nodes: list[dict[str, Any]]) -> MagicMock:
    client = MagicMock()
    client.list_nodes.return_value = nodes
    return client


@pytest.fixture(autouse=True)
def _no_node_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    slept: list[float] = []
    monkeypatch.setattr("chaotic.providers.nomad.time.sleep", slept.append)
    return slept


def test_node_drains_then_restores(_no_node_sleep: list[float]) -> None:
    client = node_client([node("n1")])
    provider = make_provider(NomadChaotic, client, node_drain_deadline_seconds=15, node_wait_for=30)

    provider.action_node()

    client.drain_node.assert_called_once_with(node_id="id-n1", deadline_seconds=15, ignore_system_jobs=True)
    client.set_node_eligibility.assert_called_once_with(node_id="id-n1", eligible=True)
    assert _no_node_sleep == [30]


def test_node_defaults() -> None:
    client = node_client([node("n1")])
    make_provider(NomadChaotic, client).action_node()

    client.drain_node.assert_called_once_with(node_id="id-n1", deadline_seconds=10, ignore_system_jobs=True)


def test_node_drain_system_jobs_inverts_ignore_system_jobs() -> None:
    client = node_client([node("n1")])
    make_provider(NomadChaotic, client, node_drain_system_jobs=True).action_node()

    assert client.drain_node.call_args.kwargs["ignore_system_jobs"] is False


def test_node_skiplist() -> None:
    client = node_client([node("keep"), node("n2")])
    provider = make_provider(NomadChaotic, client, node_skiplist=["keep"])

    assert [n["Name"] for n in provider._eligible_nodes()] == ["n2"]


def test_node_class_skiplist() -> None:
    client = node_client([node("storage-1", NodeClass="storage"), node("n2")])
    provider = make_provider(NomadChaotic, client, node_class_skiplist=["storage"])

    assert [n["Name"] for n in provider._eligible_nodes()] == ["n2"]


def test_node_without_candidates(caplog: pytest.LogCaptureFixture, _no_node_sleep: list[float]) -> None:
    make_provider(NomadChaotic, node_client([])).action_node()

    assert "No nodes found" in caplog.text
    assert _no_node_sleep == []


@pytest.mark.parametrize(
    ("percent", "node_count", "expected"),
    [
        (0, 10, 1),  # unset: exactly one node
        (30, 10, 3),
        (5, 10, 1),  # rounds down to zero, so at least one
        (100, 4, 4),
        (300, 4, 4),  # nonsense percentages are clamped
    ],
)
def test_drain_count(percent: int, node_count: int, expected: int) -> None:
    provider = make_provider(NomadChaotic, MagicMock(), node_drain_amount_in_percent=percent)
    assert provider._drain_count(node_count) == expected


def test_node_drains_a_percentage() -> None:
    client = node_client([node(f"n{i}") for i in range(10)])
    provider = make_provider(NomadChaotic, client, node_drain_amount_in_percent=30)

    provider.action_node()

    assert client.drain_node.call_count == 3
    assert client.set_node_eligibility.call_count == 3
    drained = {call.kwargs["node_id"] for call in client.drain_node.call_args_list}
    restored = {call.kwargs["node_id"] for call in client.set_node_eligibility.call_args_list}
    # Exactly the nodes that were drained get their eligibility back.
    assert drained == restored


def test_node_dry_run_touches_nothing(caplog: pytest.LogCaptureFixture, _no_node_sleep: list[float]) -> None:
    client = node_client([node("n1")])
    provider = NomadChaotic()
    provider.__dict__["client"] = client
    provider.configure(dry_run=True)

    provider.action_node()

    client.drain_node.assert_not_called()
    client.set_node_eligibility.assert_not_called()
    assert _no_node_sleep == []
    assert "Drain node: n1" in caplog.text
