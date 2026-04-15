"""
Email adapter — IMAP polling + Resend outbound for restaurant booking.

Polls a configured IMAP inbox for inbound emails about reservations
or menu questions, processes them via LLMService, and
replies via the Resend API.
"""

import email
import imaplib
import logging
import re
from email.header import decode_header
from email.utils import parseaddr
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


def _decode_header_value(raw: str) -> str:
    """Decode a MIME-encoded header into a plain string."""
    parts = decode_header(raw or '')
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            decoded.append(part)
    return ' '.join(decoded)


def _extract_text_body(msg: email.message.Message) -> str:
    """Walk a MIME message and extract the plain-text body."""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == 'text/plain':
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                return (payload or b'').decode(charset, errors='replace')
        # Fallback: try text/html
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == 'text/html':
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                html = (payload or b'').decode(charset, errors='replace')
                # Rough HTML → text
                text = re.sub(r'<[^>]+>', ' ', html)
                return re.sub(r'\s+', ' ', text).strip()
    else:
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or 'utf-8'
        return (payload or b'').decode(charset, errors='replace')
    return ''


class EmailAdapter:
    """Polls IMAP for new emails and sends replies via Resend."""

    def __init__(self) -> None:
        self.imap_server = settings.imap_server
        self.imap_email = settings.imap_email
        self.imap_password = settings.imap_password
        self.reply_from = settings.reply_from_email
        self.resend_api_key = settings.resend_api_key
        self.restaurant_name = settings.restaurant_name

    # ── IMAP ────────────────────────────────────────────────────────

    def fetch_unseen(self) -> List[Dict[str, Any]]:
        """Connect to IMAP, fetch UNSEEN emails, return parsed list."""
        if not all([self.imap_server, self.imap_email, self.imap_password]):
            logger.warning('IMAP credentials not configured — skipping fetch')
            return []

        results: List[Dict[str, Any]] = []
        try:
            conn = imaplib.IMAP4_SSL(self.imap_server)
            conn.login(self.imap_email, self.imap_password)
            conn.select('INBOX')

            status, data = conn.search(None, 'UNSEEN')
            if status != 'OK' or not data or not data[0]:
                conn.logout()
                return []

            msg_ids = data[0].split()
            logger.info('Found %d unseen emails', len(msg_ids))

            for mid in msg_ids[-20:]:  # Cap at 20 per poll
                status2, msg_data = conn.fetch(mid, '(RFC822)')
                if status2 != 'OK' or not msg_data or not msg_data[0]:
                    continue

                raw = msg_data[0][1]
                if not isinstance(raw, bytes):
                    continue

                msg = email.message_from_bytes(raw)
                from_raw = msg.get('From', '')
                from_name, from_addr = parseaddr(from_raw)
                from_name = _decode_header_value(from_name) if from_name else from_addr
                subject = _decode_header_value(msg.get('Subject', ''))
                body = _extract_text_body(msg).strip()
                message_id = msg.get('Message-ID', '')

                # Skip own replies
                if from_addr.lower() == self.imap_email.lower():
                    continue
                if from_addr.lower() == self.reply_from.lower():
                    continue

                results.append({
                    'message_id': message_id,
                    'from_email': from_addr,
                    'from_name': from_name,
                    'subject': subject,
                    'body': body[:3000],  # Trim very long emails
                    'imap_uid': mid.decode() if isinstance(mid, bytes) else str(mid),
                })

            conn.logout()
        except Exception:
            logger.exception('Error fetching IMAP emails')

        return results

    # ── Resend outbound ─────────────────────────────────────────────

    def send_reply(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        in_reply_to: Optional[str] = None,
    ) -> bool:
        """Send a reply email via Resend API."""
        if not self.resend_api_key:
            logger.warning('Resend API key not configured — reply not sent')
            return False

        import requests

        headers_dict: Dict[str, str] = {}
        if in_reply_to:
            headers_dict['In-Reply-To'] = in_reply_to
            headers_dict['References'] = in_reply_to

        try:
            resp = requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {self.resend_api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'from': f'{self.restaurant_name} <{self.reply_from}>',
                    'to': [to_email],
                    'subject': subject,
                    'text': body_text,
                    'headers': headers_dict,
                },
                timeout=15,
            )
            if resp.ok:
                logger.info('Reply sent to %s via Resend (id=%s)', to_email, resp.json().get('id'))
                return True
            else:
                logger.error('Resend error %s: %s', resp.status_code, resp.text[:200])
                return False
        except Exception:
            logger.exception('Failed to send reply via Resend')
            return False
