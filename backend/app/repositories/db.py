import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import settings


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReservationRepository:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or settings.restaurants_db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_ref TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    party_size INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    notes TEXT,
                    status TEXT NOT NULL,
                    calendar_event_id TEXT,
                    payment_method_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS payment_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reservation_id INTEGER NOT NULL,
                    stripe_payment_method_id TEXT NOT NULL,
                    brand TEXT,
                    last4 TEXT,
                    exp_month INTEGER,
                    exp_year INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(reservation_id) REFERENCES reservations(id)
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reservation_id INTEGER,
                    event_type TEXT NOT NULL,
                    payload TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(reservation_id) REFERENCES reservations(id)
                );
                """
            )

    def create_reservation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = _utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO reservations (
                    external_ref, name, phone, email, date, time, party_size,
                    source, notes, status, calendar_event_id, payment_method_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data['external_ref'],
                    data['name'],
                    data['phone'],
                    data.get('email'),
                    data['date'],
                    data['time'],
                    data['party_size'],
                    data.get('source', 'whatsapp'),
                    data.get('notes'),
                    data.get('status', 'pending_payment_method'),
                    data.get('calendar_event_id'),
                    data.get('payment_method_id'),
                    now,
                    now,
                ),
            )
            rid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        row = self.get_reservation(int(rid))
        if not row:
            raise RuntimeError('Failed to read reservation after insert')
        return row

    def get_reservation(self, reservation_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute('SELECT * FROM reservations WHERE id = ?', (reservation_id,)).fetchone()
        return dict(row) if row else None

    def get_by_external_ref(self, external_ref: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute('SELECT * FROM reservations WHERE external_ref = ?', (external_ref,)).fetchone()
        return dict(row) if row else None

    def update_reservation(self, reservation_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not updates:
            current = self.get_reservation(reservation_id)
            if not current:
                raise ValueError('Reservation not found')
            return current
        updates = {**updates, 'updated_at': _utcnow()}
        cols = ', '.join([f'{k} = ?' for k in updates.keys()])
        vals = list(updates.values()) + [reservation_id]
        with self._connect() as conn:
            conn.execute(f'UPDATE reservations SET {cols} WHERE id = ?', vals)
        row = self.get_reservation(reservation_id)
        if not row:
            raise ValueError('Reservation not found')
        return row

    def save_message(self, user_id: str, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)',
                (user_id, role, content, _utcnow()),
            )

    def save_payment_method(
        self,
        reservation_id: int,
        stripe_payment_method_id: str,
        brand: Optional[str],
        last4: Optional[str],
        exp_month: Optional[int],
        exp_year: Optional[int],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO payment_methods (
                    reservation_id, stripe_payment_method_id, brand, last4, exp_month, exp_year, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (reservation_id, stripe_payment_method_id, brand, last4, exp_month, exp_year, _utcnow()),
            )

    def add_audit_log(self, reservation_id: Optional[int], event_type: str, payload: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO audit_log (reservation_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)',
                (reservation_id, event_type, json.dumps(payload), _utcnow()),
            )
