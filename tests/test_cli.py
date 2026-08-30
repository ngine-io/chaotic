"""Tests for argument parsing and the process entry point."""

from __future__ import annotations

from typing import Any

import pytest
import truststore

from chaotic import cli
from chaotic.errors import ChaoticError, ConfigError
from chaotic.version import __version__


def parse(*argv: str) -> Any:
    return cli.build_parser().parse_args(argv)


def test_defaults_are_unset_so_env_can_take_over() -> None:
    args = parse()
    assert args.config is None
    assert args.interval is None
    assert args.periodic is False


def test_version_flag_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        parse("--version")
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_config_defaults_to_config_yaml() -> None:
    assert cli.resolve_config_source(parse()) == "config.yaml"


def test_config_falls_back_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAOTIC_CONFIG", "from-env.yaml")
    assert cli.resolve_config_source(parse()) == "from-env.yaml"


def test_explicit_config_flag_beats_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAOTIC_CONFIG", "from-env.yaml")
    assert cli.resolve_config_source(parse("--config", "from-flag.yaml")) == "from-flag.yaml"


def test_interval_defaults_to_one() -> None:
    assert cli.resolve_interval(parse()) == 1


def test_interval_falls_back_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAOTIC_INTERVAL", "60")
    assert cli.resolve_interval(parse()) == 60


def test_explicit_interval_flag_beats_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAOTIC_INTERVAL", "60")
    assert cli.resolve_interval(parse("--interval", "5")) == 5


def test_non_numeric_interval_env_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAOTIC_INTERVAL", "hourly")
    with pytest.raises(ChaoticError, match="must be an integer"):
        cli.resolve_interval(parse())


@pytest.mark.parametrize("value", ["0", "-3"])
def test_non_positive_interval_is_rejected(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("CHAOTIC_INTERVAL", value)
    with pytest.raises(ChaoticError, match="at least 1 minute"):
        cli.resolve_interval(parse())


@pytest.fixture
def _stub_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralise the side effects main() performs before doing any work."""
    monkeypatch.setattr(cli, "load_env", lambda: None)
    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    monkeypatch.setattr(truststore, "inject_into_ssl", lambda: None)


@pytest.mark.usefixtures("_stub_startup")
def test_main_runs_once_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []
    monkeypatch.setattr(cli, "run_once", seen.append)

    assert cli.main(["--config", "plan.yaml"]) == cli.EXIT_OK
    assert seen == ["plan.yaml"]


@pytest.mark.usefixtures("_stub_startup")
def test_main_runs_periodic(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}
    monkeypatch.setattr(cli, "run_periodic", lambda **kw: seen.update(kw))

    exit_code = cli.main(["--periodic", "--interval", "5", "--config", "plan.yaml"])

    assert exit_code == cli.EXIT_OK
    assert seen == {"interval": 5, "config_source": "plan.yaml"}


@pytest.mark.usefixtures("_stub_startup")
def test_main_reports_known_errors(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    def boom(_: str) -> None:
        raise ConfigError("No kind defined in config")

    monkeypatch.setattr(cli, "run_once", boom)

    assert cli.main([]) == cli.EXIT_FAILURE
    assert "No kind defined in config" in caplog.text
    # A known error is a message, not a stack trace.
    assert "Traceback" not in caplog.text


@pytest.mark.usefixtures("_stub_startup")
def test_main_reports_unexpected_errors(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    def boom(_: str) -> None:
        raise RuntimeError("the API fell over")

    monkeypatch.setattr(cli, "run_once", boom)

    assert cli.main([]) == cli.EXIT_FAILURE
    assert "the API fell over" in caplog.text
    assert "Traceback" in caplog.text


@pytest.mark.usefixtures("_stub_startup")
def test_main_exits_cleanly_on_ctrl_c(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    def interrupt(**_: Any) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "run_periodic", interrupt)

    assert cli.main(["--periodic"]) == cli.EXIT_OK
    assert "Stopping..." in caplog.text


@pytest.mark.usefixtures("_stub_startup")
def test_main_rejects_a_bad_interval_before_running(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("CHAOTIC_INTERVAL", "nope")
    monkeypatch.setattr(cli, "run_periodic", lambda **_: pytest.fail("must not run"))

    assert cli.main(["--periodic"]) == cli.EXIT_FAILURE
    assert "CHAOTIC_INTERVAL must be an integer" in caplog.text
