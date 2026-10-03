import pytest
from pydantic import ValidationError

from app.core.config import Settings


def make(**env: str) -> Settings:
    return Settings(_env_file=None, **env)


def test_defaults_are_safe_for_local_development() -> None:
    s = make()
    assert s.app_env == "development"
    assert s.log_level == "INFO"
    assert s.cors_allowed_origins == ["http://localhost:5173"]


def test_environment_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LOG_FORMAT", "json")
    s = Settings(_env_file=None)
    assert s.app_env == "production"
    assert s.log_format == "json"


def test_cors_origins_parse_from_comma_separated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://a.test, https://b.test ,")
    assert Settings(_env_file=None).cors_allowed_origins == ["http://a.test", "https://b.test"]


def test_log_level_is_case_insensitive() -> None:
    assert make(log_level="debug").log_level == "DEBUG"


@pytest.mark.parametrize("field,value", [("app_env", "staging"), ("log_level", "LOUD")])
def test_invalid_values_are_rejected(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        make(**{field: value})
