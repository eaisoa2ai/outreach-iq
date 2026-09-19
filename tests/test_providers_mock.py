from pathlib import Path

from outreachiq.providers.mock_email import MockEmailProvider
from outreachiq.providers.mock_voice import MockVoiceProvider


def test_forced_completed_outcome_produces_transcript():
    provider = MockVoiceProvider(forced_outcome="completed")
    initiation = provider.initiate_call(customer_name="Ada", phone="+15551234567", guidance_text="Ask about pacing.")
    assert initiation["status"] == "initiated"

    result = provider.wait_for_terminal_status(
        initiation["conversation_id"],
        max_wait_seconds=5,
        poll_interval_seconds=0,
        no_pickup_after_seconds=0,
    )
    assert result["outcome"] == "completed"

    transcript = provider.get_transcript(initiation["conversation_id"])
    assert "Ada" in transcript["transcript"]


def test_forced_failed_outcome_is_classified_as_failed():
    provider = MockVoiceProvider(forced_outcome="failed")
    initiation = provider.initiate_call(customer_name="Ada", phone="+15551234567", guidance_text="")
    result = provider.wait_for_terminal_status(
        initiation["conversation_id"], max_wait_seconds=5, poll_interval_seconds=0, no_pickup_after_seconds=0
    )
    assert result["outcome"] == "failed"


def test_forced_did_not_pick_outcome_times_out_as_no_pickup():
    provider = MockVoiceProvider(forced_outcome="did_not_pick")
    initiation = provider.initiate_call(customer_name="Ada", phone="+15551234567", guidance_text="")
    # no_pickup_after_seconds=0 means the very first poll should classify it
    result = provider.wait_for_terminal_status(
        initiation["conversation_id"], max_wait_seconds=5, poll_interval_seconds=0, no_pickup_after_seconds=0
    )
    assert result["outcome"] == "did_not_pick"


def test_outcome_is_deterministic_per_phone_number():
    provider_a = MockVoiceProvider()
    provider_b = MockVoiceProvider()
    phone = "+15559998888"

    def resolve(provider):
        init = provider.initiate_call(customer_name="Ada", phone=phone, guidance_text="")
        return provider.wait_for_terminal_status(
            init["conversation_id"], max_wait_seconds=5, poll_interval_seconds=0, no_pickup_after_seconds=0
        )["outcome"]

    assert resolve(provider_a) == resolve(provider_b)


def test_unknown_conversation_id_reports_failed():
    provider = MockVoiceProvider()
    status = provider.get_call_status("does-not-exist")
    assert status["raw_status"] == "failed"


def test_mock_email_provider_writes_outbox_file(tmp_path, monkeypatch):
    import outreachiq.providers.mock_email as mock_email_module

    monkeypatch.setattr(mock_email_module, "OUTBOX_DIR", tmp_path)
    provider = MockEmailProvider()

    result = provider.send_email(
        to="ada@example.com", sender="outreach@outreachiq.example.com", subject="Hi", html_body="<p>Hello</p>"
    )

    assert result["status"] == "sent"
    written_files = list(Path(tmp_path).glob("*.html"))
    assert len(written_files) == 1
    assert "Hello" in written_files[0].read_text()


def test_mock_email_provider_fails_without_body():
    provider = MockEmailProvider()
    result = provider.send_email(to="ada@example.com", sender="x@example.com", subject="Hi", html_body="")
    assert result["status"] == "failed"
