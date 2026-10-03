import json
import logging

import pytest

from app.core.logging import JsonFormatter, configure_logging


def test_json_formatter_emits_valid_json_with_extra_fields() -> None:
    record = logging.LogRecord("app.test", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    record.duration_ms = 12.5
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["duration_ms"] == 12.5
    assert "timestamp" in payload


def test_configure_logging_is_idempotent() -> None:
    root = logging.getLogger()
    configure_logging("INFO", "json")
    configure_logging("DEBUG", "console")
    ours = [h for h in root.handlers if getattr(h, "_app_handler", False)]
    assert len(ours) == 1
    assert root.level == logging.DEBUG
    configure_logging("INFO", "console")


def test_json_output_reaches_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "json")
    logging.getLogger("app.test").info("structured", extra={"document_id": 7})
    line = capsys.readouterr().out.strip().splitlines()[-1]
    assert json.loads(line)["document_id"] == 7
    configure_logging("INFO", "console")
