from outreachiq.config import Settings, Thresholds, _load_thresholds


def test_thresholds_have_sane_defaults():
    thresholds = Thresholds()
    assert 0.0 < thresholds.confidence_floor < 1.0
    assert thresholds.max_call_wait_seconds > thresholds.call_poll_interval_seconds
    assert thresholds.no_pickup_after_seconds > 0


def test_thresholds_load_from_project_yaml():
    thresholds = _load_thresholds()
    assert thresholds.confidence_floor == 0.6
    assert thresholds.days_back_default == 30


def test_settings_default_to_mock_providers(monkeypatch):
    monkeypatch.delenv("VOICE_PROVIDER", raising=False)
    monkeypatch.delenv("EMAIL_PROVIDER", raising=False)
    settings = Settings(_env_file=None)
    assert settings.voice_provider == "mock"
    assert settings.email_provider == "mock"
    assert settings.default_country_code == "+1"


def test_settings_do_not_require_openai_key_to_construct():
    settings = Settings(_env_file=None, openai_api_key=None)
    assert settings.openai_api_key is None
