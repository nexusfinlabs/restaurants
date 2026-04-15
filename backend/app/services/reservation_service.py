from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from app.models.schemas import ReservationCreate
from app.repositories.db import ReservationRepository
from app.services.calendar_service import CalendarService


class ReservationService:
    def __init__(self, repo: ReservationRepository) -> None:
        self.repo = repo
        self.calendar = CalendarService()

    def create(self, data: ReservationCreate) -> Dict[str, Any]:
        external_ref = f"rsv_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid4().hex[:8]}"
        reservation = self.repo.create_reservation(
            {
                'external_ref': external_ref,
                'name': data.name,
                'phone': data.phone,
                'email': str(data.email) if data.email else None,
                'date': data.date,
                'time': data.time,
                'party_size': data.party_size,
                'source': data.source,
                'notes': data.notes,
                'status': 'pending_payment_method',
            }
        )
        self.repo.add_audit_log(reservation['id'], 'reservation_created', {'external_ref': external_ref})
        return reservation

    def confirm(self, reservation_id: int) -> Dict[str, Any]:
        reservation = self.repo.get_reservation(reservation_id)
        if not reservation:
            raise ValueError('Reservation not found')

        existing_event_id = reservation.get('calendar_event_id')
        if existing_event_id:
            updated = self.repo.update_reservation(reservation_id, {'status': 'confirmed'})
            self.repo.add_audit_log(reservation_id, 'reservation_confirmed', {'provider': 'idempotent'})
            return updated

        event = self.calendar.create_event(reservation)
        updated = self.repo.update_reservation(
            reservation_id,
            {
                'status': 'confirmed',
                'calendar_event_id': event['event_id'],
            },
        )
        self.repo.add_audit_log(reservation_id, 'reservation_confirmed', event)
        return updated
