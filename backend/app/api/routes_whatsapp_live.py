"""
WhatsApp Webhook — Direct HTTP endpoint for OpenClaw forwarding.

OpenClaw gateway is configured to POST incoming WhatsApp messages
to this endpoint instead of (or in addition to) logging to file.

Architecture:
  WhatsApp → OpenClaw Gateway → POST /webhooks/whatsapp/inbound
  → LLMService (Ollama + menu.json)
  → reply via OpenClaw CLI (openclaw message send)

This decouples from the command_router.py log-tailing approach.
"""
import json
import logging
import os
import subprocess
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.config import settings
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/webhooks/whatsapp', tags=['whatsapp-live'])

# OpenClaw CLI path (on VPS)
OPENCLAW_NODE_PATH = os.getenv(
    'OPENCLAW_NODE_PATH',
    '/home/albi_agent/.nvm/versions/node/v22.22.0/bin',
)


class InboundMessage(BaseModel):
    """Payload from OpenClaw gateway webhook or manual test."""
    sender: str           # e.g. "34605693177" or "34605693177@s.whatsapp.net"
    body: str             # message text
    timestamp: Optional[int] = None
    channel: str = 'whatsapp'


class WebhookResponse(BaseModel):
    status: str
    reply: Optional[str] = None


def _send_via_openclaw(message: str, channel: str = 'whatsapp', target: str = '34605693177'):
    """Send a reply back via OpenClaw CLI."""
    try:
        env = os.environ.copy()
        env['PATH'] = f"{OPENCLAW_NODE_PATH}:{env.get('PATH', '')}"
        result = subprocess.run(
            ['openclaw', 'message', 'send',
             '--channel', channel,
             '--target', target,
             '--message', message],
            timeout=30, env=env, capture_output=True,
        )
        if result.returncode == 0:
            logger.info('Reply sent via OpenClaw (%d chars)', len(message))
        else:
            logger.error('OpenClaw send failed: %s', result.stderr.decode()[:200])
    except FileNotFoundError:
        logger.warning('OpenClaw CLI not found — reply not sent (dev mode)')
    except Exception as e:
        logger.error('OpenClaw send error: %s', e)


@router.post('/inbound', response_model=WebhookResponse)
async def whatsapp_inbound(msg: InboundMessage):
    """
    Receive a WhatsApp message forwarded by OpenClaw gateway.
    Process with Ollama LLM using restaurant menu context.
    Reply via OpenClaw CLI.
    """
    body = msg.body.strip()
    sender = msg.sender.replace('@s.whatsapp.net', '').lstrip('+')

    logger.info('WA inbound from %s: %s', sender[-4:], body[:80])

    # Skip if it's a command (let command_router handle those)
    if body.startswith('!'):
        return WebhookResponse(status='skipped_command')

    # Process with LLM
    llm = LLMService()

    # Detect intent
    intent = llm.detect_intent(body)

    if intent == 'menu_qa':
        reply = llm.ask_menu(body)
    else:
        # Reservation or general inquiry
        slots = llm.extract_reservation_slots(body)
        missing = [k for k, v in slots.items() if v is None and k in ('date', 'time', 'party_size')]

        if not missing:
            # Create reservation
            reply = (
                f"¡Genial! 🎉 He registrado tu solicitud:\n"
                f"📅 {slots['date']} a las {slots['time']}\n"
                f"👥 {slots['party_size']} personas\n"
                f"📱 {slots.get('phone', 'pendiente')}\n\n"
                f"Para confirmar, necesitamos una garantía de 20€ "
                f"(se descuenta de la cuenta). "
                f"Te envío el enlace de pago por aquí mismo.\n\n"
                f"¿Alguna alergia o restricción alimentaria?"
            )
        else:
            # Ask for missing info via LLM for a more natural response
            reply = llm.ask_menu(
                f"El cliente quiere reservar pero no ha dado: {', '.join(missing)}. "
                f"Su mensaje: {body}. "
                f"Pídele amablemente la información que falta."
            )

    # Send reply via OpenClaw
    _send_via_openclaw(reply, channel=msg.channel, target=sender)

    return WebhookResponse(status='replied', reply=reply)
