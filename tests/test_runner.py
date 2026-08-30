"""Tests for the one-shot and periodic runners."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, ClassVar

import pytest
import schedule

from chaotic import runner
from chaotic.errors import ConfigError, UnknownProviderError
from chaotic.factory import ChaoticFactory
from chaotic.providers.base import Chaotic


class RecordingChaotic(Chaotic):
    """Records how it was configured and how often it acted."""

    instances: ClassVar[list[RecordingChaotic]] = []

    def __init__(self) -> None:
        super().__init__()
        self.actions = 0
        RecordingChaotic.instances.append(self)

    def action(self) -> None:
        self.actions += 1


@pytest.fixture(autouse=True)
def _clean_schedule() -> Any:
    schedule.clear()
    RecordingChaotic.instances = []
    yield
    schedule.clear()


@pytest.fixture
def registered(monkeypatch: pytest.MonkeyPatch) -> type[RecordingChaotic]:
    monkeypatch.setitem(ChaoticFactory.CLOUD_CLASSES, "recording", RecordingChaotic)
    return RecordingChaotic


def stop_the_loop(*, on_capture: Any = None) -> Any:
    """A `time.sleep` stub that ends the periodic loop after the first tick.

    `schedule.run_all()` itself sleeps zero seconds between jobs, so only a real
    tick (a positive duration) must break out.
    """

    def fake_sleep(seconds: float) -> None:
        if seconds <= 0:
            return
        if on_capture is not None:
            on_capture()
        raise KeyboardInterrupt

    return fake_sleep


def write_plan(tmp_path: Path, **overrides: Any) -> str:
    plan = {"kind": "recording", "dry_run": True, "configs": {"tag": "chaos"}, **overrides}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    return str(path)


def test_run_once_configures_and_acts(tmp_path: Path, registered: type[RecordingChaotic]) -> None:
    runner.run_once(write_plan(tmp_path, excludes={"weekdays": []}))

    (instance,) = registered.instances
    assert instance.actions == 1
    assert instance.dry_run is True
    assert instance.configs == {"tag": "chaos"}
    assert instance.excludes == {"weekdays": []}


def test_run_once_propagates_config_errors(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("dry_run: true\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        runner.run_once(str(path))


def test_run_once_propagates_unknown_kinds(tmp_path: Path) -> None:
    with pytest.raises(UnknownProviderError):
        runner.run_once(write_plan(tmp_path, kind="aws"))


def test_run_once_rereads_the_config_every_time(tmp_path: Path, registered: type[RecordingChaotic]) -> None:
    path = Path(write_plan(tmp_path))
    runner.run_once(str(path))
    path.write_text(json.dumps({"kind": "recording", "dry_run": False}), encoding="utf-8")
    runner.run_once(str(path))

    first, second = registered.instances
    assert first.dry_run is True
    assert second.dry_run is False


def test_guarded_run_swallows_and_logs_failures(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    runner._run_once_guarded(str(tmp_path / "missing.yaml"))

    assert "Chaos run failed, continuing with the next interval" in caplog.text


def test_run_periodic_runs_immediately_then_schedules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, registered: type[RecordingChaotic]
) -> None:
    monkeypatch.setattr(time, "sleep", stop_the_loop())
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)

    with pytest.raises(KeyboardInterrupt):
        runner.run_periodic(interval=5, config_source=write_plan(tmp_path))

    (instance,) = registered.instances
    assert instance.actions == 1
    # The loop clears its jobs on the way out.
    assert schedule.jobs == []


def test_run_periodic_registers_the_requested_interval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, registered: type[RecordingChaotic]
) -> None:
    seen: dict[str, Any] = {}

    def capture() -> None:
        seen["jobs"] = [(job.interval, job.unit) for job in schedule.jobs]

    monkeypatch.setattr(time, "sleep", stop_the_loop(on_capture=capture))
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)

    with pytest.raises(KeyboardInterrupt):
        runner.run_periodic(interval=7, config_source=write_plan(tmp_path))

    assert seen["jobs"] == [(7, "minutes")]


def test_run_periodic_survives_a_broken_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(time, "sleep", stop_the_loop())
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)

    with pytest.raises(KeyboardInterrupt):
        runner.run_periodic(interval=1, config_source=str(tmp_path / "missing.yaml"))

    assert "continuing with the next interval" in caplog.text


def test_heartbeat_only_on_a_tty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, registered: type[RecordingChaotic], capsys: Any
) -> None:
    monkeypatch.setattr(time, "sleep", stop_the_loop())
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    with pytest.raises(KeyboardInterrupt):
        runner.run_periodic(interval=1, config_source=write_plan(tmp_path))

    assert "." in capsys.readouterr().out
