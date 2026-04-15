# Nexus Lounge — Reservation Platform

Sistema completo de reservas para **Nexus Lounge**, restaurante gourmet en Madrid.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + SQLite + Resend + Google Calendar API + Stripe |
| Frontend | HTML/CSS/JS vanilla |
| Email | HTML responsive (dark theme) vía Resend |
| Pagos | Stripe Payment Link (garantía no-show) |
| Calendario | Google Calendar Service Account |

## Estructura

```
restaurants/
├── backend/          # FastAPI app (puerto 8090)
│   ├── app/
│   │   ├── api/      # Rutas REST
│   │   ├── services/ # Calendar, Email, LLM, Reservations
│   │   ├── adapters/ # IMAP polling + Resend outbound
│   │   └── config.py
│   ├── .env.example
│   └── requirements.txt
└── frontend/         # Web estática
    ├── index.html
    ├── styles.css
    ├── app.js
    └── config.js     ← edita API URL y Stripe aquí
```

## Inicio rápido

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # rellena RESEND_API_KEY, GOOGLE_*, STRIPE_*
uvicorn app.main:app --reload --host 0.0.0.0 --port 8090

# Frontend
# Edita frontend/config.js → RESTAURANT_API_URL
# Abre frontend/index.html en un servidor estático (ej. live-server)
```

## Variables clave (.env)

| Variable | Descripción |
|---|---|
| `RESTAURANT_NAME` | `Nexus Lounge` |
| `REPLY_FROM_EMAIL` | `alobo@nexusfinlabs.com` |
| `RESEND_API_KEY` | Clave API de Resend |
| `GOOGLE_CALENDAR_ID` | ID del calendario destino |
| `GOOGLE_CREDENTIALS_PATH` | JSON service account |
| `STRIPE_SECRET_KEY` | Clave Stripe (sk_live_...) |

## Flujo de reserva

1. Cliente rellena el modal → **POST /reservations** → crea entrada en SQLite  
2. Backend llama a **POST /reservations/{id}/confirm** → crea evento en Google Calendar  
3. Se envía email HTML premium a cliente desde `alobo@nexusfinlabs.com`  
4. Email incluye **Magic Link de Stripe** para el depósito de garantía (no-show)  
5. Stripe notifica via webhook cuando el pago es completado  

## Contacto

`alobo@nexusfinlabs.com` · WhatsApp +34 663 103 334
