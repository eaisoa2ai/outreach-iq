"""Writes emails to ./outbox instead of sending them — lets anyone clone the
repo and see exactly what the Email agent produced without any credentials.
"""
from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any

from outreachiq.config import PROJECT_ROOT
from outreachiq.providers.base import EmailProvider

OUTBOX_DIR = PROJECT_ROOT / "outbox"


class MockEmailProvider(EmailProvider):
    def send_email(self, *, to: str, sender: str, subject: str, html_body: str) -> dict[str, Any]:
        if not to or not html_body:
            return {"status": "failed", "message_id": None, "error": "Missing recipient or body"}

        OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
        message_id = f"mock-{uuid.uuid4().hex[:12]}"
        safe_recipient = re.sub(r"[^a-zA-Z0-9_.@-]", "_", to)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        path = OUTBOX_DIR / f"{timestamp}_{safe_recipient}.html"
        path.write_text(
            f"<!-- To: {to} | From: {sender} | Subject: {subject} -->\n{html_body}",
            encoding="utf-8",
        )
        return {"status": "sent", "message_id": message_id, "path": str(path)}
