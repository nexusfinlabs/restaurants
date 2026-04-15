# Restaurants Reservations MVP

Servicio FastAPI para reservas con:

- Webhook WhatsApp mock: `POST /webhooks/whatsapp/mock`
- CRUD basico de reservas: `POST /reservations`, `GET /reservations/{id}`
- Confirmacion + evento en Google Calendar (o mock): `POST /reservations/{id}/confirm`
- Tokenizacion no-show (Stripe SetupIntent o mock): `POST /reservations/setup-intent`
- Preguntas de menu con Ollama: `POST /menu/ask`

La configuracion lee primero `ai-agents/.env` y luego `restaurants/.env` (este ultimo tiene prioridad).

## Instalacion

```bash
cd ai-agents/restaurants
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8090
```

## Variables relevantes

| Variable | Uso |
| --- | --- |
| `RESTAURANTS_DB_PATH` | SQLite (por defecto `./data/restaurants.db`) |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Menu QA via `/api/generate` |
| `GOOGLE_CALENDAR_ID` | Calendario destino |
| `GOOGLE_CREDENTIALS_PATH` o `GOOGLE_APPLICATION_CREDENTIALS` | JSON service account |
| `STRIPE_SECRET_KEY` | SetupIntent real; sin clave, modo mock |

## Ejemplos rapidos

```bash
curl -s localhost:8090/health

curl -s -X POST localhost:8090/webhooks/whatsapp/mock \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"u1","message":"Reserva 2026-04-20 21:00 2 personas +34600000000"}'

curl -s -X POST localhost:8090/menu/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Hay opcion vegana?"}'
```

## Seguridad

No se almacenan PAN ni CVV. Solo `payment_method_id` de Stripe y metadatos (`brand`, `last4`, expiracion).
