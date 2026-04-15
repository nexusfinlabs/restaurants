from datetime import datetime, timedelta
from typing import Any, Dict

from app.config import settings


def _parse_start(reservation: Dict[str, Any]) -> datetime:
    date_s = str(reservation['date'])
    time_s = str(reservation['time'])
    if len(time_s) == 5:
        time_s = f'{time_s}:00'
    return datetime.fromisoformat(f'{date_s}T{time_s}')


class CalendarService:
    def create_event(self, reservation: Dict[str, Any]) -> Dict[str, str]:
        creds_path = settings.google_credentials_path or settings.google_application_credentials
        if creds_path and settings.google_calendar_id:
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build

                credentials = service_account.Credentials.from_service_account_file(
                    creds_path,
                    scopes=['https://www.googleapis.com/auth/calendar'],
                )
                service = build('calendar', 'v3', credentials=credentials)
                start = _parse_start(reservation)
                end = start + timedelta(minutes=90)
                event = {
                    'summary': f"Reserva {reservation['name']} ({reservation['party_size']} pax)",
                    'description': f"Ref: {reservation['external_ref']} | Tel: {reservation['phone']}",
                    'start': {'dateTime': start.isoformat(), 'timeZone': 'Europe/Madrid'},
                    'end': {'dateTime': end.isoformat(), 'timeZone': 'Europe/Madrid'},
                }
                created = service.events().insert(calendarId=settings.google_calendar_id, body=event).execute()
                return {'event_id': str(created.get('id', '')), 'provider': 'google'}
            except Exception:
                pass

        return {'event_id': f"mock-{reservation['external_ref']}", 'provider': 'mock'}
