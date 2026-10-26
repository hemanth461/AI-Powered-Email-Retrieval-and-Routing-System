"""
Gmail API integration.

Handles:
  - OAuth2 authentication (installed-app flow, token cached to disk)
  - Fetching unread emails with sender/receiver/subject/body/timestamp/attachments
  - Marking messages as read once processed
  - Forwarding (routing) an email to a department mailbox

Setup required before this will work:
  1. Create a Google Cloud project, enable the Gmail API.
  2. Create an OAuth Client ID (type: Desktop App).
  3. Download the JSON and save it to the path in GMAIL_CREDENTIALS_PATH (.env).
  4. On first run, a browser window opens for consent; the resulting token is
     cached to GMAIL_TOKEN_PATH so future runs are non-interactive.
"""
import base64
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import settings

logger = logging.getLogger(__name__)

# Scopes: read unread mail, mark as read, and send (forward) on the user's behalf
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


class GmailService:
    def __init__(self):
        self.creds: Optional[Credentials] = None
        self.service = None

    def _resolve_paths(self):
        token_candidates = [
            "/etc/secrets/gmail_token.json",
            settings.gmail_token_path,
            "gmail_token.json",
        ]
        cred_candidates = [
            "/etc/secrets/gmail_credentials.json",
            settings.gmail_credentials_path,
            "gmail_credentials.json",
        ]

        token_path = next((p for p in token_candidates if os.path.exists(p)), settings.gmail_token_path)
        cred_path = next((p for p in cred_candidates if os.path.exists(p)), settings.gmail_credentials_path)
        return token_path, cred_path

    def authenticate(self):
        """Load cached token, refresh it, or run the interactive OAuth flow."""
        token_path, cred_path = self._resolve_paths()
        creds = None

        # Auto-hydrate credentials from environment variables if present
        if not os.path.exists(token_path) and os.environ.get("GMAIL_TOKEN_DATA"):
            os.makedirs(os.path.dirname(token_path) or ".", exist_ok=True)
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(os.environ["GMAIL_TOKEN_DATA"])

        if not os.path.exists(cred_path) and os.environ.get("GMAIL_CREDENTIALS_DATA"):
            os.makedirs(os.path.dirname(cred_path) or ".", exist_ok=True)
            with open(cred_path, "w", encoding="utf-8") as f:
                f.write(os.environ["GMAIL_CREDENTIALS_DATA"])

        # Re-check paths after hydration
        token_path, cred_path = self._resolve_paths()

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(cred_path):
                    raise FileNotFoundError(
                        f"Gmail OAuth client secret not found. Looked in {cred_path}, /etc/secrets/gmail_credentials.json, and {settings.gmail_credentials_path}."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
                creds = flow.run_local_server(port=0)

            os.makedirs(os.path.dirname(token_path) or ".", exist_ok=True)
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())

        self.creds = creds
        self.service = build("gmail", "v1", credentials=creds)
        return self.service

    def _ensure_service(self):
        if self.service is None:
            self.authenticate()
        return self.service

    def fetch_unread_emails(self, max_results: int = 20) -> list:
        """
        Fetch unread emails from the monitored inbox.
        Returns a list of dicts: sender, receiver, subject, body, timestamp,
        gmail_message_id, thread_id, has_attachments, attachment_names.
        """
        service = self._ensure_service()
        emails = []

        try:
            response = (
                service.users()
                .messages()
                .list(userId="me", labelIds=["UNREAD", "INBOX"], maxResults=max_results)
                .execute()
            )
            messages = response.get("messages", [])

            for msg_meta in messages:
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg_meta["id"], format="full")
                    .execute()
                )
                emails.append(self._parse_message(msg))

        except HttpError as e:
            logger.error(f"Gmail API error while fetching unread emails: {e}")
            raise

        return emails

    def _parse_message(self, msg: dict) -> dict:
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}

        body_text = self._extract_body(msg["payload"])
        attachments = self._extract_attachment_names(msg["payload"])

        return {
            "gmail_message_id": msg["id"],
            "thread_id": msg.get("threadId"),
            "sender": headers.get("from", "unknown"),
            "receiver": headers.get("to", settings.gmail_monitored_account),
            "subject": headers.get("subject", "(no subject)"),
            "body": body_text,
            "timestamp": headers.get("date"),
            "has_attachments": len(attachments) > 0,
            "attachment_names": ", ".join(attachments) if attachments else None,
        }

    @staticmethod
    def _clean_html(html_text: str) -> str:
        """Strip HTML tags, scripts, styles, and unescape HTML entities."""
        if not html_text:
            return ""
        import html
        import re
        # Remove script and style elements
        text = re.sub(r'<(script|style|head)[^>]*>.*?</\1>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # Convert break and paragraph tags to newlines
        text = re.sub(r'<br\s*/?>|</p>|</div>|</tr>|</li>', '\n', text, flags=re.IGNORECASE)
        # Remove all remaining HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Unescape HTML entities (e.g. &amp;, &nbsp;, &#39;)
        text = html.unescape(text)
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        return text.strip()

    def _extract_body(self, payload: dict) -> str:
        """Walk the (possibly nested multipart) payload for the plain text body, falling back to cleaned HTML."""
        # 1. Prefer explicit text/plain
        if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
            raw = self._decode_base64(payload["body"]["data"])
            return self._clean_html(raw) if "<" in raw and ">" in raw else raw

        # 2. Check parts for text/plain first
        for part in payload.get("parts", []) or []:
            if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                raw = self._decode_base64(part["body"]["data"])
                return self._clean_html(raw) if "<" in raw and ">" in raw else raw

        # 3. Fallback to text/html with HTML cleaning
        if payload.get("mimeType") == "text/html" and "data" in payload.get("body", {}):
            raw = self._decode_base64(payload["body"]["data"])
            return self._clean_html(raw)

        # 4. Recursively check nested parts
        for part in payload.get("parts", []) or []:
            text = self._extract_body(part)
            if text:
                return text
        return ""

    @staticmethod
    def _decode_base64(data: str) -> str:
        try:
            return base64.urlsafe_b64decode(data.encode("UTF-8")).decode("UTF-8", errors="replace")
        except Exception:
            return ""

    @staticmethod
    def _extract_attachment_names(payload: dict) -> list:
        names = []

        def walk(part):
            filename = part.get("filename")
            if filename:
                names.append(filename)
            for sub in part.get("parts", []) or []:
                walk(sub)

        walk(payload)
        return names

    def mark_as_read(self, message_id: str):
        service = self._ensure_service()
        service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    def forward_email(self, original_subject: str, original_body: str, original_sender: str,
                       to_address: str, department_name: str):
        """Forward/route the email to a department mailbox via the Gmail API."""
        service = self._ensure_service()

        message = MIMEMultipart()
        message["to"] = to_address
        message["subject"] = f"[Routed: {department_name}] {original_subject}"

        forward_note = (
            f"This email was automatically routed to the {department_name} team "
            f"by the Email Triage System.\n\n"
            f"Original sender: {original_sender}\n"
            f"---------- Forwarded message ----------\n\n"
            f"{original_body}"
        )
        message.attach(MIMEText(forward_note, "plain"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            service.users().messages().send(userId="me", body={"raw": raw}).execute()
            return True, None
        except HttpError as e:
            logger.error(f"Failed to forward email to {to_address}: {e}")
            return False, str(e)
