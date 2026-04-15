from fastapi import APIRouter, HTTPException

from app.api.dependencies import get_payment_service, get_repo, get_reservation_service
from app.models.schemas import ConfirmReservationRequest, ReservationCreate, SetupIntentRequest, SetupIntentResponse

router = APIRouter(prefix='/reservations', tags=['reservations'])


from app.adapters.email_adapter import EmailAdapter


def _build_confirmation_html(
    name: str,
    ref: str,
    date: str,
    time: str,
    party_size: int,
    phone: str,
    stripe_url: str,
) -> str:
    """Generate a premium HTML confirmation email for Nexus Lounge."""
    stripe_block = ""
    if stripe_url:
        stripe_block = f"""
        <tr>
          <td style="padding: 0 40px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="background: linear-gradient(135deg, #c9a84c 0%, #f0c96e 100%); border-radius: 10px; padding: 24px; text-align: center;">
                  <p style="margin: 0 0 6px; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px; color: #1a1208; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;">Confirma tu reserva</p>
                  <p style="margin: 0 0 18px; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px; color: #3b2c0a; line-height: 1.5;">Completa el depósito de garantía (no-show) para asegurar tu mesa. Es rápido y seguro.</p>
                  <a href="{stripe_url}"
                     style="display: inline-block; background: #1a1208; color: #c9a84c; text-decoration: none; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 14px; font-weight: 700; letter-spacing: 0.05em; padding: 14px 32px; border-radius: 6px; border: 2px solid #c9a84c;">
                    &#x1F511;&nbsp; Pagar garantía con Stripe
                  </a>
                  <p style="margin: 14px 0 0; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11px; color: #5a4210; line-height: 1.4;">Transacción segura · Powered by Stripe · Sin guardar datos de tarjeta</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>"""
    else:
        stripe_block = ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Reserva confirmada — Nexus Lounge</title>
</head>
<body style="margin:0; padding:0; background-color:#0d0d0d; font-family:'Helvetica Neue', Arial, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d0d0d; padding: 40px 16px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; background:#161616; border-radius:16px; overflow:hidden; border:1px solid #2a2a2a;">

          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(160deg, #1c1400 0%, #0d0d0d 60%); padding: 40px 40px 30px; text-align: center; border-bottom: 1px solid #2a2a2a;">
              <p style="margin: 0 0 8px; font-size: 11px; letter-spacing: 0.25em; color: #c9a84c; text-transform: uppercase; font-weight: 600;">Experiencia gastronómica</p>
              <h1 style="margin: 0; font-size: 34px; font-weight: 300; color: #f5e9cc; letter-spacing: 0.06em;">Nexus<span style="font-weight:700; color:#c9a84c;">Lounge</span></h1>
              <p style="margin: 12px 0 0; font-size: 13px; color: #6b6b6b; letter-spacing: 0.05em;">Madrid · Cocina de autor</p>
            </td>
          </tr>

          <!-- Status badge -->
          <tr>
            <td style="padding: 28px 40px 0; text-align: center;">
              <span style="display:inline-block; background:#1a2e1a; color:#4ade80; font-size:12px; font-weight:600; letter-spacing:0.1em; text-transform:uppercase; padding:8px 20px; border-radius:20px; border:1px solid #2d5a2d;">
                ✓ &nbsp;Solicitud recibida
              </span>
            </td>
          </tr>

          <!-- Greeting -->
          <tr>
            <td style="padding: 24px 40px 20px; text-align: center;">
              <h2 style="margin: 0 0 8px; font-size: 20px; font-weight: 400; color: #e8dcc8; letter-spacing: 0.02em;">Hola, {name}</h2>
              <p style="margin: 0; font-size: 14px; color: #888; line-height: 1.6;">Tu solicitud de reserva ha sido registrada con referencia</p>
              <p style="margin: 8px 0 0; font-size: 17px; font-weight: 700; color: #c9a84c; letter-spacing: 0.08em; font-family: monospace;">{ref}</p>
            </td>
          </tr>

          <!-- Divider -->
          <tr><td style="padding: 0 40px;"><hr style="border:none; border-top:1px solid #2a2a2a; margin:0;" /></td></tr>

          <!-- Reservation details -->
          <tr>
            <td style="padding: 28px 40px 24px;">
              <p style="margin: 0 0 16px; font-size: 11px; letter-spacing: 0.15em; text-transform: uppercase; color: #555; font-weight: 600;">Detalles de la reserva</p>
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding: 10px 16px; background:#1e1e1e; border-radius:8px 8px 0 0; border-bottom:1px solid #2a2a2a;">
                    <span style="font-size:18px;">📅</span>
                    <span style="font-size:13px; color:#aaa; margin-left:10px;">Fecha</span>
                    <span style="float:right; font-size:14px; font-weight:600; color:#e8dcc8;">{date}</span>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; background:#1e1e1e; border-bottom:1px solid #2a2a2a;">
                    <span style="font-size:18px;">🕐</span>
                    <span style="font-size:13px; color:#aaa; margin-left:10px;">Hora</span>
                    <span style="float:right; font-size:14px; font-weight:600; color:#e8dcc8;">{time}</span>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; background:#1e1e1e; border-bottom:1px solid #2a2a2a;">
                    <span style="font-size:18px;">👥</span>
                    <span style="font-size:13px; color:#aaa; margin-left:10px;">Personas</span>
                    <span style="float:right; font-size:14px; font-weight:600; color:#e8dcc8;">{party_size}</span>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; background:#1e1e1e; border-radius:0 0 8px 8px;">
                    <span style="font-size:18px;">📞</span>
                    <span style="font-size:13px; color:#aaa; margin-left:10px;">Teléfono</span>
                    <span style="float:right; font-size:14px; font-weight:600; color:#e8dcc8;">{phone}</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Divider -->
          <tr><td style="padding: 0 40px;"><hr style="border:none; border-top:1px solid #2a2a2a; margin:0;" /></td></tr>

          <!-- Stripe CTA -->
          {stripe_block}

          <!-- Info note -->
          <tr>
            <td style="padding: 0 40px 28px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:#1a1a1a; border-left: 3px solid #c9a84c; border-radius:4px; padding:16px 20px;">
                    <p style="margin:0; font-size:13px; color:#888; line-height:1.6;">
                      ¿Tienes alguna alergia o restricción alimentaria? Responde a este email
                      o escríbenos por WhatsApp y lo gestionamos antes de tu visita.<br/><br/>
                      Para cancelar o modificar, menciona la referencia <strong style="color:#c9a84c;">{ref}</strong>.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Divider -->
          <tr><td style="padding: 0 40px;"><hr style="border:none; border-top:1px solid #2a2a2a; margin:0;" /></td></tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 24px 40px; text-align:center;">
              <p style="margin: 0 0 4px; font-size:13px; color:#555; line-height:1.6;">Nos alegra tenerte pronto en</p>
              <p style="margin: 0 0 16px; font-size:15px; font-weight:500; color:#c9a84c; letter-spacing:0.04em;">Nexus Lounge · Madrid</p>
              <p style="margin: 0; font-size:11px; color:#3d3d3d; letter-spacing:0.05em;">© 2026 Nexus Lounge · alobo@nexusfinlabs.com</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _build_confirmation_text(
    name: str,
    ref: str,
    date: str,
    time: str,
    party_size: int,
    phone: str,
    stripe_url: str,
) -> str:
    """Plain-text fallback for the confirmation email."""
    lines = [
        f"Hola {name},",
        "",
        f"Tu reserva ha sido recibida con referencia {ref}.",
        "",
        f"  📅 Fecha:    {date}",
        f"  🕐 Hora:     {time}",
        f"  👥 Personas: {party_size}",
        f"  📞 Teléfono: {phone}",
        "",
    ]
    if stripe_url:
        lines += [
            "Para confirmar definitivamente, realiza el depósito de garantía (no-show):",
            stripe_url,
            "",
        ]
    lines += [
        "Si tienes alguna alergia o restricción alimentaria, responde a este email.",
        "",
        "Saludos,",
        "Equipo Nexus Lounge",
    ]
    return "\n".join(lines)


@router.post('')
def create_reservation(payload: ReservationCreate):
    service = get_reservation_service()
    reservation = service.create(payload)

    # Send confirmation email if email is provided
    if payload.email:
        ref = reservation.get('external_ref', '')

        import urllib.parse
        stripe_base = "https://buy.stripe.com/test_eVq8wPbkPf9RaEP2eI7N600"
        stripe_ref = f"NEXUS_LOUNGE|{reservation.get('date', '')}|{reservation.get('time', '')}"
        stripe_url = f"{stripe_base}?client_reference_id={urllib.parse.quote(stripe_ref)}"

        html_body = _build_confirmation_html(
            name=payload.name,
            ref=ref,
            date=payload.date,
            time=payload.time,
            party_size=payload.party_size,
            phone=payload.phone,
            stripe_url=stripe_url,
        )
        text_body = _build_confirmation_text(
            name=payload.name,
            ref=ref,
            date=payload.date,
            time=payload.time,
            party_size=payload.party_size,
            phone=payload.phone,
            stripe_url=stripe_url,
        )

        try:
            adapter = EmailAdapter()
            # Send HTML + text via Resend
            import requests
            from app.config import settings
            resp = requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {settings.resend_api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'from': f'Nexus Lounge <alobo@nexusfinlabs.com>',
                    'to': [str(payload.email)],
                    'subject': f'Reserva recibida — Nexus Lounge [Ref: {ref}]',
                    'html': html_body,
                    'text': text_body,
                },
                timeout=15,
            )
            if not resp.ok:
                pass  # Log silently, don't fail the booking
        except Exception:
            pass  # Don't fail the reservation if email breaks

    return reservation


@router.get('/{reservation_id}')
def get_reservation(reservation_id: int):
    repo = get_repo()
    reservation = repo.get_reservation(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail='Reservation not found')
    return reservation


@router.post('/{reservation_id}/confirm')
def confirm_reservation(reservation_id: int, payload: ConfirmReservationRequest):
    repo = get_repo()
    reservation = repo.get_reservation(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail='Reservation not found')

    if payload.payment_method_id:
        payment = get_payment_service().attach_payment_method(payload.payment_method_id)
        repo.save_payment_method(
            reservation_id,
            str(payment['payment_method_id']),
            payment.get('brand'),
            payment.get('last4'),
            payment.get('exp_month'),
            payment.get('exp_year'),
        )
        repo.update_reservation(reservation_id, {'payment_method_id': str(payment['payment_method_id'])})

    try:
        return get_reservation_service().confirm(reservation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/setup-intent', response_model=SetupIntentResponse)
def create_setup_intent(payload: SetupIntentRequest):
    repo = get_repo()
    reservation = repo.get_reservation(payload.reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail='Reservation not found')

    email = payload.customer_email or reservation.get('email')
    result = get_payment_service().create_setup_intent(payload.reservation_id, str(email) if email else None)
    return result
