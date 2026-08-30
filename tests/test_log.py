"""Tests for logging setup."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from chaotic.log import configure_logging, log

LOGGING_INI = """\
[loggers]
keys=root

[handlers]
keys=stream_handler

[formatters]
keys=simple

[logger_root]
level=WARNING
handlers=stream_handler

[handler_stream_handler]
class=StreamHandler
level=WARNING
formatter=simple
args=(sys.stderr,)

[formatter_simple]
format=%(levelname)s %(message)s
"""


@pytest.fixture
def _restore_logging() -> Iterator[None]:
    """Undo whatever configure_logging() does to the root logger.

    The handlers are detached for the duration of the test so that
    `basicConfig(force=True)` cannot close pytest's own capture handlers.
    """
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    root.handlers[:] = []
    try:
        yield
    finally:
        root.handlers[:] = handlers
        root.setLevel(level)


@pytest.mark.usefixtures("_restore_logging")
def test_uses_a_config_file_when_present(tmp_path: Path) -> None:
    path = tmp_path / "logging.ini"
    path.write_text(LOGGING_INI, encoding="utf-8")

    assert configure_logging(path) is log
    assert logging.getLogger().level == logging.WARNING


@pytest.mark.usefixtures("_restore_logging")
def test_config_file_keeps_existing_loggers_alive(tmp_path: Path) -> None:
    path = tmp_path / "logging.ini"
    path.write_text(LOGGING_INI, encoding="utf-8")

    configure_logging(path)
    # fileConfig disables pre-existing loggers by default; chaotic's own logger
    # is created at import time and must survive.
    assert log.disabled is False


@pytest.mark.usefixtures("_restore_logging")
def test_falls_back_to_basic_config(tmp_path: Path) -> None:
    assert configure_logging(tmp_path / "absent.ini", level="debug") is log
    assert logging.getLogger().level == logging.DEBUG


@pytest.mark.usefixtures("_restore_logging")
def test_level_comes_from_the_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAOTIC_LOG_LEVEL", "warning")
    configure_logging(tmp_path / "absent.ini")
    assert logging.getLogger().level == logging.WARNING


@pytest.mark.usefixtures("_restore_logging")
def test_config_path_comes_from_the_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "custom.ini"
    path.write_text(LOGGING_INI, encoding="utf-8")
    monkeypatch.setenv("CHAOTIC_LOG_CONFIG", str(path))

    configure_logging()

    assert logging.getLogger().level == logging.WARNING


def test_importing_does_not_configure_anything() -> None:
    # The module level logger must exist without any handler of its own, so that
    # library users keep control of their logging setup.
    assert log.name == "chaotic"
    assert log.handlers == []


@pytest.mark.usefixtures("_restore_logging")
def test_shipped_logging_ini_is_usable(capsys: pytest.CaptureFixture[str]) -> None:
    """The repository's own logging.ini must load and emit JSON.

    It references a python-json-logger class by dotted path, which no linter or
    type checker would catch if the library moved it again.
    """
    configure_logging(Path(__file__).resolve().parent.parent / "logging.ini")
    log.info("hello")

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["message"] == "hello"
    assert payload["levelname"] == "INFO"
