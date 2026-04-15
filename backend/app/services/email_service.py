"""
Email service — process inbound emails with LLM and create reservations.

Orchestrates the flow:
  IMAP inbound → LLMService (intent + slots) → ReservationService → email reply
"""

import logging
from typing import Any, Dict, Optional

from app.adapters.email_adapter import EmailAdapter
from app.models.schemas import ReservationCreate
from app.repositories.db import ReservationRepository
from app.services.llm_service import LLMService
from app.services.reservation_service import ReservationService

logger = logging.getLogger(__name__)


class EmailService:
    """Process inbound emails: intent detection → reservation or menu Q&A → auto-reply."""

    def __init__(
        self,
        repo: ReservationRepository,
        reservation_service: ReservationService,
        llm_service: LLMService,
    ) -> None:
        self.repo = repo
        self.reservation_service = reservation_service
        self.llm_service = llm_service
        self.adapter = EmailAdapter()

    def poll_and_process(self) -> int:
        """Fetch unseen emails, process each, return count of processed."""
        emails = self.adapter.fetch_unseen()
        processed = 0

        for em in emails:
            try:
                self._process_one(em)
                processed += 1
            except Exception:
                logger.exception('Error processing email from %s', em.get('from_email'))

        return processed

    def _process_one(self, em: Dict[str, Any]) -> None:
        """Process a single inbound email."""
        from_email = em['from_email']
        from_name = em.get('from_name', from_email)
        subject = em.get('subject', '')
        body = em.get('body', '')
        message_id = em.get('message_id')

        # Combine subject + body for intent detection
        full_text = f"{subject}\n{body}".strip()
        if not full_text:
            return

        # Log inbound
        self.repo.save_message(from_email, 'user', full_text)
        self.repo.add_audit_log(None, 'email_inbound', {
            'from': from_email,
            'subject': subject,
        })

        # Detect intent
        intent = self.llm_service.detect_intent(full_text)
        logger.info('Email from %s → intent=%s', from_email, intent)

        if intent == 'menu_qa':
            reply_text = self._handle_menu_question(full_text, from_name)
        else:
            reply_text = self._handle_reservation(full_text, from_email, from_name)

        # Send reply
        reply_subject = f'Re: {subject}' if subject else 'Respuesta de Nexus Lounge'
        sent = self.adapter.send_reply(
            to_email=from_email,
            subject=reply_subject,
            body_text=reply_text,
            in_reply_to=message_id,
        )

        # Log outbound
        self.repo.save_message(from_email, 'assistant', reply_text)
        self.repo.add_audit_log(None, 'email_reply', {
            'to': from_email,
            'sent': sent,
            'intent': intent,
        })

    def _handle_menu_question(self, text: str, from_name: str) -> str:
        """Use LLM to answer a menu question."""
        answer = self.llm_service.ask_menu(text)
        return (
            f'Hola {from_name},\n\n'
            f'{answer}\n\n'
            'Si tienes más preguntas o quieres reservar, responde a este email '
            'o escríbenos por WhatsApp al +34 663 103 334.\n\n'
            'Un saludo,\n'
            'Equipo Nexus Lounge'
        )

    def _handle_reservation(self, text: str, from_email: str, from_name: str) -> str:
        """Try to extract reservation slots and create a booking."""
        slots = self.llm_service.extract_reservation_slots(text)
        missing = [k for k in ('date', 'time', 'party_size') if not slots.get(k)]

        if missing:
            missing_str = ', '.join(missing)
            return (
                f'Hola {from_name},\n\n'
                'Gracias por tu interés en reservar en Nexus Lounge.\n\n'
                f'Para completar tu reserva, me falta: {missing_str}.\n\n'
                'Por ejemplo: "Quiero reservar para el 20 de abril a las 21:00 '
                'para 2 personas, teléfono +34600000000".\n\n'
                'También puedes reservar directamente por WhatsApp al +34 663 103 334.\n\n'
                'Un saludo,\n'
                'Equipo Nexus Lounge'
            )

        # Create the reservation
        phone = slots.get('phone') or 'pendiente'
        reservation = self.reservation_service.create(
            ReservationCreate(
                name=from_name or f'Email-{from_email.split("@")[0]}',
                phone=phone,
                email=from_email,
                date=str(slots['date']),
                time=str(slots['time']),
                party_size=int(slots['party_size']),
                source='email',
                notes=f'Reserva creada por email desde {from_email}',
            )
        )

        ref = reservation['external_ref']
        return (
            f'Hola {from_name},\n\n'
            f'¡Tu reserva ha sido creada con referencia {ref}!\n\n'
            f'📅 Fecha: {slots["date"]}\n'
            f'🕐 Hora: {slots["time"]}\n'
            f'👥 Personas: {slots["party_size"]}\n\n'
            'Para confirmar definitivamente, necesitamos un método de pago '
            '(garantía de no-show). Puedes enviarnos los datos por WhatsApp '
            'al +34 663 103 334 o responder a este email.\n\n'
            'Si necesitas modificar o cancelar, indícanos la referencia '
            f'{ref}.\n\n'
            'Un saludo,\n'
            'Equipo Nexus Lounge'
        )
