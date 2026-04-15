from typing import Any, Dict

from app.models.schemas import ReservationCreate
from app.services.llm_service import LLMService
from app.services.reservation_service import ReservationService


class WhatsAppMockAdapter:
    def __init__(self, reservation_service: ReservationService, llm_service: LLMService):
        self.reservation_service = reservation_service
        self.llm_service = llm_service

    def handle_message(self, user_id: str, message: str) -> Dict[str, Any]:
        intent = self.llm_service.detect_intent(message)
        if intent == 'menu_qa':
            answer = self.llm_service.ask_menu(message)
            return {'type': 'menu_answer', 'reply': answer}

        slots = self.llm_service.extract_reservation_slots(message)
        missing = [k for k in ('date', 'time', 'party_size', 'phone') if not slots.get(k)]
        if missing:
            return {
                'type': 'request_missing_info',
                'reply': (
                    'Para reservar me faltan: '
                    + ', '.join(missing)
                    + '. Ejemplo: 2026-04-20 a las 21:00 para 2 personas, telefono +34600000000.'
                ),
            }

        suffix = user_id[-4:] if len(user_id) >= 4 else user_id
        reservation = self.reservation_service.create(
            ReservationCreate(
                name=f'Cliente-{suffix}',
                phone=str(slots['phone']),
                email=slots.get('email'),
                date=str(slots['date']),
                time=str(slots['time']),
                party_size=int(slots['party_size']),
                source='whatsapp',
                notes='Created via WhatsApp mock',
            )
        )
        return {
            'type': 'reservation_created',
            'reply': (
                f"Reserva creada con referencia {reservation['external_ref']}. "
                'Siguiente paso: confirma con metodo de pago tokenizado para politica de no-show '
                f"(POST /reservations/{reservation['id']}/confirm con payment_method_id)."
            ),
            'reservation_id': str(reservation['id']),
        }
