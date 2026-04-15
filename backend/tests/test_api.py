from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_module(module):
    db_path = Path(__file__).resolve().parent / 'test_restaurants.db'
    if db_path.exists():
        db_path.unlink()


def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_whatsapp_reservation_flow():
    payload = {
        'user_id': 'user-123',
        'message': 'Quiero reservar para 2026-04-20 21:00 2 personas, mi tel es +34600000000',
    }
    response = client.post('/webhooks/whatsapp/mock', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data['type'] == 'reservation_created'
    assert 'reservation_id' in data


def test_create_setup_intent_mock():
    create = client.post(
        '/reservations',
        json={
            'name': 'Alberto',
            'phone': '+34600000000',
            'date': '2026-04-20',
            'time': '22:00',
            'party_size': 2,
            'source': 'whatsapp',
        },
    )
    assert create.status_code == 200
    rid = create.json()['id']
    response = client.post('/reservations/setup-intent', json={'reservation_id': rid})
    assert response.status_code == 200
    body = response.json()
    assert body['setup_intent_id'].startswith(('set_', 'seti_'))


def test_confirm_reservation_with_payment():
    create = client.post(
        '/reservations',
        json={
            'name': 'Alberto',
            'phone': '+34600000000',
            'date': '2026-04-21',
            'time': '20:30',
            'party_size': 3,
            'source': 'api',
        },
    )
    rid = create.json()['id']
    confirm = client.post(f'/reservations/{rid}/confirm', json={'payment_method_id': 'pm_test_mock'})
    assert confirm.status_code == 200
    assert confirm.json()['status'] == 'confirmed'
    assert confirm.json()['calendar_event_id']
