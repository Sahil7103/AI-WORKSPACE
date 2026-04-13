"""
Gmail integration service using Google OAuth.
"""

from base64 import urlsafe_b64decode
from datetime import datetime, UTC, timedelta
from email.utils import parsedate_to_datetime
import asyncio
import imaplib
import json
import os
import re
from typing import Optional
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

import httpx
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import GmailConnection, Document
from app.services.document_service import DocumentService
from app.utils.logger import logger


class GmailAuthError(ValueError):
    """Raised when Gmail rejects the supplied credentials."""


class GmailOAuthError(ValueError):
    """Raised when Google OAuth cannot be completed."""


class GmailService:
    """Service for connecting to Gmail and importing messages as documents."""

    GOOGLE_OAUTH_SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
    ]

    @staticmethod
    def _allow_insecure_oauth_transport_for_localhost() -> None:
        """Allow HTTP OAuth redirects for localhost development only."""
        redirect_uri = (settings.google_oauth_redirect_uri or "").strip().lower()
        frontend_url = (settings.frontend_url or "").strip().lower()
        is_local_dev = (
            redirect_uri.startswith("http://localhost")
            or redirect_uri.startswith("http://127.0.0.1")
            or frontend_url.startswith("http://localhost")
            or frontend_url.startswith("http://127.0.0.1")
        )
        if is_local_dev:
            os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

    @staticmethod
    async def get_connection(db: AsyncSession, user_id: int) -> Optional[GmailConnection]:
        """Get Gmail connection for a user."""
        stmt = select(GmailConnection).where(GmailConnection.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    def _get_google_client_config() -> dict:
        """Load Google OAuth client configuration from settings."""
        try:
            raw = json.loads(settings.google_credentials_json or "{}")
        except json.JSONDecodeError as exc:
            raise GmailOAuthError("GOOGLE_CREDENTIALS_JSON is not valid JSON") from exc

        if "web" in raw:
            return {"web": raw["web"]}
        if "installed" in raw:
            return {"installed": raw["installed"]}

        raise GmailOAuthError(
            "GOOGLE_CREDENTIALS_JSON must contain a Google OAuth web or installed client configuration"
        )

    @staticmethod
    def _encode_state(
        user_id: int,
        next_path: str,
        code_verifier: Optional[str] = None,
    ) -> str:
        """Create a signed state token for the Gmail OAuth flow."""
        payload = {
            "sub": str(user_id),
            "next_path": next_path or "/chat",
            "purpose": "gmail_oauth",
            "exp": datetime.utcnow() + timedelta(minutes=15),
        }
        if code_verifier:
            payload["code_verifier"] = code_verifier
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def _decode_state(state: str) -> dict:
        """Decode and validate an OAuth state token."""
        try:
            payload = jwt.decode(
                state,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
        except JWTError as exc:
            raise GmailOAuthError("Invalid Gmail OAuth state") from exc

        if payload.get("purpose") != "gmail_oauth":
            raise GmailOAuthError("Invalid Gmail OAuth state")

        return payload

    @staticmethod
    def _extract_token_payload(secret: str) -> Optional[str]:
        """Extract an OAuth refresh token from stored connection secrets."""
        normalized = (secret or "").strip()
        if normalized.startswith("oauth:"):
            return normalized.split("oauth:", 1)[1]
        return None

    @staticmethod
    def build_oauth_authorization_url(user_id: int, next_path: str = "/chat") -> str:
        """Build the Google OAuth URL for Gmail connection."""
        GmailService._allow_insecure_oauth_transport_for_localhost()
        try:
            from google_auth_oauthlib.flow import Flow
        except Exception as exc:
            raise GmailOAuthError(
                "Google OAuth dependencies are not installed. Run pip install -r backend/requirements.txt"
            ) from exc

        client_config = GmailService._get_google_client_config()
        flow = Flow.from_client_config(
            client_config,
            scopes=GmailService.GOOGLE_OAUTH_SCOPES,
        )
        flow.redirect_uri = settings.google_oauth_redirect_uri

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=GmailService._encode_state(user_id, next_path),
        )
        parsed = urlparse(auth_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["state"] = GmailService._encode_state(
            user_id,
            next_path,
            code_verifier=getattr(flow, "code_verifier", None),
        )
        return urlunparse(parsed._replace(query=urlencode(query)))

    @staticmethod
    async def upsert_oauth_connection(
        db: AsyncSession,
        user_id: int,
        gmail_address: str,
        refresh_token: str,
    ) -> GmailConnection:
        """Create or update a user's Gmail OAuth connection."""
        connection = await GmailService.get_connection(db, user_id)
        stored_secret = f"oauth:{refresh_token.strip()}"

        if connection is None:
            connection = GmailConnection(
                user_id=user_id,
                gmail_address=gmail_address.strip(),
                app_password=stored_secret,
                is_active=True,
            )
            db.add(connection)
        else:
            connection.gmail_address = gmail_address.strip()
            connection.app_password = stored_secret
            connection.is_active = True

        await db.commit()
        await db.refresh(connection)
        return connection

    @staticmethod
    async def disconnect(db: AsyncSession, user_id: int) -> None:
        """Disable a user's Gmail connection without deleting imported docs."""
        connection = await GmailService.get_connection(db, user_id)
        if connection:
            connection.is_active = False
            await db.commit()

    @staticmethod
    async def mark_connection_inactive(db: AsyncSession, user_id: int) -> None:
        """Mark a Gmail connection inactive after a failed auth attempt."""
        connection = await GmailService.get_connection(db, user_id)
        if connection:
            connection.is_active = False
            await db.commit()

    @staticmethod
    async def complete_oauth_callback(
        db: AsyncSession,
        code: str,
        state: str,
        authorization_response: Optional[str] = None,
    ) -> tuple[GmailConnection, str]:
        """Exchange a Google OAuth code and persist the resulting connection."""
        GmailService._allow_insecure_oauth_transport_for_localhost()
        try:
            from google_auth_oauthlib.flow import Flow
        except Exception as exc:
            raise GmailOAuthError(
                "Google OAuth dependencies are not installed. Run pip install -r backend/requirements.txt"
            ) from exc

        payload = GmailService._decode_state(state)
        user_id = int(payload["sub"])
        next_path = payload.get("next_path") or "/chat"
        code_verifier = payload.get("code_verifier")

        client_config = GmailService._get_google_client_config()
        flow = Flow.from_client_config(
            client_config,
            scopes=GmailService.GOOGLE_OAUTH_SCOPES,
            state=state,
        )
        flow.redirect_uri = settings.google_oauth_redirect_uri

        try:
            fetch_kwargs = {}
            if authorization_response:
                fetch_kwargs["authorization_response"] = authorization_response
            else:
                fetch_kwargs["code"] = code
            if code_verifier:
                fetch_kwargs["code_verifier"] = code_verifier

            await asyncio.to_thread(flow.fetch_token, **fetch_kwargs)
        except Exception as exc:
            logger.error(f"Google OAuth token exchange failed: {str(exc)}")
            raise GmailOAuthError(f"Google OAuth token exchange failed: {str(exc)}") from exc

        credentials = flow.credentials
        refresh_token = credentials.refresh_token
        if not refresh_token:
            existing = await GmailService.get_connection(db, user_id)
            refresh_token = (
                GmailService._extract_token_payload(existing.app_password)
                if existing
                else None
            )

        if not refresh_token:
            raise GmailOAuthError(
                "Google did not return a refresh token. Reconnect and approve consent again."
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            profile_response = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/profile",
                headers={"Authorization": f"Bearer {credentials.token}"},
            )
            profile_response.raise_for_status()
            profile = profile_response.json()

        gmail_address = profile.get("emailAddress")
        if not gmail_address:
            raise GmailOAuthError("Unable to determine the connected Gmail address")

        connection = await GmailService.upsert_oauth_connection(
            db,
            user_id=user_id,
            gmail_address=gmail_address,
            refresh_token=refresh_token,
        )
        imported_count = await GmailService.sync_inbox(db, user_id, limit=20)
        logger.info(f"Gmail OAuth connected for user {user_id}; imported {imported_count} emails")
        return connection, next_path

    @staticmethod
    def _decode_gmail_payload_text(payload: dict) -> str:
        """Extract readable text from a Gmail API message payload."""
        def decode_data(data: Optional[str]) -> str:
            if not data:
                return ""
            padded = data + "=" * (-len(data) % 4)
            try:
                return urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")
            except Exception:
                return ""

        mime_type = payload.get("mimeType", "")
        body = payload.get("body") or {}
        data = decode_data(body.get("data"))

        if mime_type == "text/plain" and data.strip():
            return data.strip()

        parts = payload.get("parts") or []
        text_parts = []
        for part in parts:
            text = GmailService._decode_gmail_payload_text(part)
            if text:
                text_parts.append(text)

        if data.strip():
            text_parts.insert(0, data.strip())

        combined = "\n\n".join(part.strip() for part in text_parts if part and part.strip())
        combined = re.sub(r"\n{3,}", "\n\n", combined)
        return combined.strip()

    @staticmethod
    async def _refresh_google_access_token(refresh_token: str) -> str:
        """Refresh an OAuth access token using the stored refresh token."""
        def refresh():
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials

            credentials = Credentials(
                None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=GmailService._extract_google_client_value("client_id"),
                client_secret=GmailService._extract_google_client_value("client_secret"),
                scopes=GmailService.GOOGLE_OAUTH_SCOPES,
            )
            credentials.refresh(Request())
            return credentials.token

        return await asyncio.to_thread(refresh)

    @staticmethod
    def _extract_google_client_value(key: str) -> str:
        """Extract a field from the configured Google OAuth client."""
        client_config = GmailService._get_google_client_config()
        outer_key = "web" if "web" in client_config else "installed"
        value = client_config[outer_key].get(key)
        if not value:
            raise GmailOAuthError(f"Missing Google OAuth client field: {key}")
        return value

    @staticmethod
    async def _load_recent_messages_oauth(
        refresh_token: str,
        limit: int,
    ) -> list[dict]:
        """Fetch recent Gmail messages using the Gmail API."""
        access_token = await GmailService._refresh_google_access_token(refresh_token)

        async with httpx.AsyncClient(timeout=60.0) as client:
            list_response = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"maxResults": limit, "labelIds": "INBOX"},
            )
            list_response.raise_for_status()
            message_refs = list_response.json().get("messages", [])

            messages = []
            for ref in message_refs:
                detail_response = await client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{ref['id']}",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={"format": "full"},
                )
                detail_response.raise_for_status()
                payload = detail_response.json()

                headers = payload.get("payload", {}).get("headers", [])
                header_map = {item.get("name", "").lower(): item.get("value", "") for item in headers}
                subject = header_map.get("subject") or "No Subject"
                from_value = header_map.get("from") or ""
                date_value = header_map.get("date")
                sent_at = None
                if date_value:
                    try:
                        sent_at = parsedate_to_datetime(date_value)
                    except Exception:
                        sent_at = None

                body = GmailService._decode_gmail_payload_text(payload.get("payload", {}))
                if not body:
                    body = payload.get("snippet", "").strip()
                if not body:
                    continue

                messages.append(
                    {
                        "message_id": payload.get("id") or ref["id"],
                        "subject": subject,
                        "from": from_value,
                        "sent_at": sent_at,
                        "body": body,
                    }
                )

            return messages

    @staticmethod
    async def _load_recent_messages_imap(
        gmail_address: str,
        app_password: str,
        limit: int,
    ) -> list[dict]:
        """Fetch recent Gmail messages via IMAP for legacy app-password connections."""
        def fetch_messages():
            mail = None
            try:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(gmail_address, app_password)
                mail.select("INBOX")

                status, data = mail.search(None, "ALL")
                if status != "OK":
                    return []

                message_ids = data[0].split()
                recent_ids = list(reversed(message_ids[-limit:]))
                parsed_messages = []

                from email import message_from_bytes
                from email.header import decode_header, make_header

                def decode_header_value(value: Optional[str]) -> str:
                    if not value:
                        return ""
                    try:
                        return str(make_header(decode_header(value)))
                    except Exception:
                        return value

                def extract_text_from_message(message) -> str:
                    text_parts = []
                    if message.is_multipart():
                        for part in message.walk():
                            content_type = part.get_content_type()
                            disposition = str(part.get("Content-Disposition") or "")
                            if "attachment" in disposition.lower():
                                continue
                            if content_type == "text/plain":
                                payload = part.get_payload(decode=True) or b""
                                charset = part.get_content_charset() or "utf-8"
                                text_parts.append(payload.decode(charset, errors="replace"))
                    else:
                        payload = message.get_payload(decode=True) or b""
                        charset = message.get_content_charset() or "utf-8"
                        text_parts.append(payload.decode(charset, errors="replace"))

                    text = "\n\n".join(part.strip() for part in text_parts if part and part.strip())
                    text = re.sub(r"\n{3,}", "\n\n", text)
                    return text.strip()

                for imap_id in recent_ids:
                    status, msg_data = mail.fetch(imap_id, "(RFC822)")
                    if status != "OK" or not msg_data:
                        continue

                    raw_email = msg_data[0][1]
                    email_message = message_from_bytes(raw_email)
                    message_id = decode_header_value(email_message.get("Message-ID"))
                    subject = decode_header_value(email_message.get("Subject")) or "No Subject"
                    from_value = decode_header_value(email_message.get("From"))
                    date_value = email_message.get("Date")

                    sent_at = None
                    if date_value:
                        try:
                            sent_at = parsedate_to_datetime(date_value)
                        except Exception:
                            sent_at = None

                    body = extract_text_from_message(email_message)
                    if not body:
                        continue

                    parsed_messages.append(
                        {
                            "message_id": message_id or f"imap-{imap_id.decode()}",
                            "subject": subject,
                            "from": from_value,
                            "sent_at": sent_at,
                            "body": body,
                        }
                    )

                return parsed_messages
            except imaplib.IMAP4.error as exc:
                message = exc.args[0] if exc.args else "Authentication failed"
                if isinstance(message, bytes):
                    message = message.decode("utf-8", errors="replace")
                lowered = str(message).lower()
                if "authenticationfailed" in lowered or "invalid credentials" in lowered:
                    raise GmailAuthError(
                        "Gmail rejected the login. Use your Gmail address and a Google App Password with IMAP enabled."
                    ) from exc
                raise GmailAuthError(str(message)) from exc
            finally:
                if mail is not None:
                    try:
                        mail.logout()
                    except Exception:
                        pass

        return await asyncio.to_thread(fetch_messages)

    @staticmethod
    async def sync_inbox(db: AsyncSession, user_id: int, limit: int = 20) -> int:
        """Sync recent Gmail messages into user-scoped documents."""
        connection = await GmailService.get_connection(db, user_id)
        if not connection or not connection.is_active:
            raise ValueError("Gmail is not connected for this user")

        refresh_token = GmailService._extract_token_payload(connection.app_password)
        if refresh_token:
            messages = await GmailService._load_recent_messages_oauth(refresh_token, limit)
        else:
            messages = await GmailService._load_recent_messages_imap(
                connection.gmail_address,
                connection.app_password,
                limit,
            )

        imported_count = 0
        for item in messages:
            file_path = f"gmail://{connection.gmail_address}/{item['message_id']}"
            existing_stmt = select(Document).where(
                Document.uploaded_by_id == user_id,
                Document.file_path == file_path,
            )
            existing_result = await db.execute(existing_stmt)
            existing_document = existing_result.scalars().first()
            if existing_document:
                continue

            sent_label = ""
            if item["sent_at"]:
                try:
                    sent_label = item["sent_at"].astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
                except Exception:
                    sent_label = str(item["sent_at"])

            content = (
                f"Subject: {item['subject']}\n"
                f"From: {item['from']}\n"
                f"Date: {sent_label}\n\n"
                f"{item['body']}"
            ).strip()

            document = await DocumentService.create_document(
                db,
                filename=f"Gmail - {item['subject'][:120]}",
                file_path=file_path,
                file_type="gmail",
                size_bytes=len(content.encode("utf-8")),
                uploaded_by_id=user_id,
                content=content,
            )

            if content:
                await DocumentService.process_document(db, document.id, content)

            imported_count += 1

        connection.last_synced_at = datetime.now(UTC).replace(tzinfo=None)
        await db.commit()
        logger.info(f"Imported {imported_count} Gmail messages for user {user_id}")
        return imported_count

    @staticmethod
    def build_frontend_callback_redirect(next_path: str, success: bool, message: str = "") -> str:
        """Build the frontend URL used after Gmail OAuth completes."""
        cleaned_path = next_path if next_path.startswith("/") else f"/{next_path}"
        status_value = "connected" if success else "error"
        suffix = f"?gmail={status_value}"
        if message:
            suffix += f"&gmail_message={quote(message)}"
        return f"{settings.frontend_url.rstrip('/')}{cleaned_path}{suffix}"
