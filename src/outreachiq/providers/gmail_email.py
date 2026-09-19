"""Real backend: Gmail API via OAuth2.

Imports google-auth/google-api-python-client lazily — only required when
EMAIL_PROVIDER=gmail. Install with: uv sync --extra gmail
"""
from __future__ import annotations

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from outreachiq.config import settings
from outreachiq.providers.base import EmailProvider

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailEmailProvider(EmailProvider):
    def __init__(self) -> None:
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "The Google API packages are required for EMAIL_PROVIDER=gmail. "
                "Install them with: uv sync --extra gmail"
            ) from exc

        import os

        creds = None
        if os.path.exists(settings.google_token_file):
            creds = Credentials.from_authorized_user_file(settings.google_token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.google_credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(settings.google_token_file, "w") as token:
                token.write(creds.to_json())

        self._service = build("gmail", "v1", credentials=creds)

    def send_email(self, *, to: str, sender: str, subject: str, html_body: str) -> dict[str, Any]:
        message = MIMEMultipart("alternative")
        message["to"] = to
        message["from"] = sender
        message["subject"] = subject or "No Subject"
        message.attach(MIMEText(html_body, "html"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        try:
            result = self._service.users().messages().send(userId="me", body={"raw": raw}).execute()
            return {"status": "sent", "message_id": result.get("id")}
        except Exception as exc:
            return {"status": "failed", "message_id": None, "error": str(exc)}
