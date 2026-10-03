from app.core.config import PROJECT_ROOT, Settings


def test_env_example_is_valid_settings() -> None:
    """The documented example must parse; catches drift between .env.example and Settings."""
    settings = Settings(_env_file=PROJECT_ROOT / ".env.example")
    assert settings.app_env == "development"
    assert settings.cors_allowed_origins == ["http://localhost:5173"]
