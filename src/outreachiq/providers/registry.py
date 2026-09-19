"""Selects the configured provider implementation. Tools call these functions
instead of importing a specific backend, which is what makes the pipeline
runnable end-to-end with zero external credentials by default.
"""
from __future__ import annotations

from functools import lru_cache

from outreachiq.config import settings
from outreachiq.providers.base import EmailProvider, VoiceProvider
from outreachiq.providers.mock_email import MockEmailProvider
from outreachiq.providers.mock_voice import MockVoiceProvider


@lru_cache
def get_voice_provider() -> VoiceProvider:
    if settings.voice_provider == "elevenlabs":
        from outreachiq.providers.elevenlabs_voice import ElevenLabsVoiceProvider

        return ElevenLabsVoiceProvider()
    return MockVoiceProvider()


@lru_cache
def get_email_provider() -> EmailProvider:
    if settings.email_provider == "gmail":
        from outreachiq.providers.gmail_email import GmailEmailProvider

        return GmailEmailProvider()
    return MockEmailProvider()
