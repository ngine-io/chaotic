"""Tests for the shared provider behaviour."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from chaotic.providers.base import Chaotic, RestartChaotic, Target


class FakeRestart(RestartChaotic):
    """A restart provider whose calls are recorded instead of performed."""

    target_noun = "widget"

    def __init__(self, targets: Sequence[Target] = (), skip: str | None = None) -> None:
        super().__init__()
        self.targets = list(targets)
        self.skip = skip
        self.calls: list[str] = []

    def list_targets(self) -> Sequence[Target]:
        return self.targets

    def stop(self, target: Target) -> None:
        self.calls.append(f"stop:{target.name}")

    def start(self, target: Target) -> None:
        self.calls.append(f"start:{target.name}")

    def skip_reason(self, target: Target) -> str | None:
        return self.skip


ONE = Target(id="1", name="one", raw={"n": 1})
TWO = Target(id="2", name="two")


def test_chaotic_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        Chaotic()  # type: ignore[abstract]


def test_configure_defaults() -> None:
    provider = FakeRestart()
    provider.configure()
    assert provider.configs == {}
    assert provider.excludes == {}
    assert provider.dry_run is False


def test_configure_stores_the_plan() -> None:
    provider = FakeRestart()
    provider.configure(configs={"tag": "chaos"}, dry_run=True, excludes={"weekdays": []})
    assert provider.configs == {"tag": "chaos"}
    assert provider.dry_run is True


def test_configure_forces_dry_run_inside_an_exclude_window(caplog: pytest.LogCaptureFixture) -> None:
    provider = FakeRestart()
    provider.configure(dry_run=False, excludes={"times_of_day": ["00:00-23:59"]})

    assert provider.dry_run is True
    assert "forcing dry-run" in caplog.text


def test_configure_keeps_dry_run_off_outside_exclude_windows() -> None:
    provider = FakeRestart()
    provider.configure(dry_run=False, excludes={"weekdays": []})
    assert provider.dry_run is False


def test_wait_before_restart_defaults_to_60() -> None:
    provider = FakeRestart()
    provider.configure()
    assert provider.wait_before_restart == 60


def test_wait_before_restart_is_coerced_to_int() -> None:
    provider = FakeRestart()
    provider.configure(configs={"wait_before_restart": "5"})
    assert provider.wait_before_restart == 5


def test_action_stops_waits_and_starts(no_sleep: list[float]) -> None:
    provider = FakeRestart([ONE])
    provider.configure(configs={"wait_before_restart": 7})

    provider.action()

    assert provider.calls == ["stop:one", "start:one"]
    assert no_sleep == [7]


def test_action_without_targets_does_nothing(caplog: pytest.LogCaptureFixture, no_sleep: list[float]) -> None:
    provider = FakeRestart([])
    provider.configure()

    provider.action()

    assert provider.calls == []
    assert no_sleep == []
    assert "No widgets found" in caplog.text


def test_action_in_dry_run_touches_nothing(caplog: pytest.LogCaptureFixture, no_sleep: list[float]) -> None:
    provider = FakeRestart([ONE])
    provider.configure(dry_run=True)

    provider.action()

    assert provider.calls == []
    assert no_sleep == []
    assert "Dry-run, not restarting widget one" in caplog.text


def test_action_honours_skip_reason(caplog: pytest.LogCaptureFixture, no_sleep: list[float]) -> None:
    provider = FakeRestart([ONE], skip="too young")
    provider.configure()

    provider.action()

    assert provider.calls == []
    assert no_sleep == []
    assert "Skipping widget one: too young" in caplog.text


def test_action_picks_a_random_target(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    monkeypatch.setattr("chaotic.providers.base.random.choice", lambda seq: seq[-1])
    provider = FakeRestart([ONE, TWO])
    provider.configure()

    provider.action()

    assert provider.calls == ["stop:two", "start:two"]


def test_action_logs_the_selected_target(caplog: pytest.LogCaptureFixture, no_sleep: list[float]) -> None:
    provider = FakeRestart([ONE])
    provider.configure()

    provider.action()

    assert "Selected widget one" in caplog.text
    assert "done" in caplog.text


def test_target_is_hashable_and_frozen() -> None:
    with pytest.raises(AttributeError):
        ONE.name = "other"  # type: ignore[misc]
