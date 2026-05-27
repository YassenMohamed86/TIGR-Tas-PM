import pytest
import os
from pydantic import ValidationError
from app.config.settings import Settings

def test_settings_loads_from_env():
    # We can load manually or rely on pytest env
    os.environ["APP_ENV"] = "testing"
    os.environ["DEBUG"] = "true"
    settings = Settings()
    assert settings.app_env == "testing"
    assert settings.debug is True

def test_missing_required_setting_raises_error():
    # Temporarily unset POSTGRES_PASSWORD
    old_pw = os.environ.pop("POSTGRES_PASSWORD", None)
    try:
        with pytest.raises(ValidationError):
            Settings()
    finally:
        if old_pw:
            os.environ["POSTGRES_PASSWORD"] = old_pw

def test_database_url_computed_correctly():
    settings = Settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert "test_user" in settings.database_url

def test_is_production_returns_false_in_testing():
    os.environ["APP_ENV"] = "testing"
    settings = Settings()
    assert settings.is_production is False

def test_is_production_returns_true_in_production():
    os.environ["APP_ENV"] = "production"
    settings = Settings()
    assert settings.is_production is True
    os.environ["APP_ENV"] = "testing" # reset

def test_allowed_extensions_parsed_as_list():
    os.environ["ALLOWED_EXTENSIONS"] = "fa,fasta,fastq"
    settings = Settings()
    assert settings.allowed_extensions == ["fa", "fasta", "fastq"]
