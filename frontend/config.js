/**
 * Nexus Lounge — Frontend Config
 * Edita estos valores para tu entorno.
 */

/** WhatsApp Business: solo dígitos, prefijo país, sin + ni espacios. */
window.RESTAURANT_WHATSAPP = '34663103334';

window.RESTAURANT_WHATSAPP_MESSAGE =
  'Hola, me gustaría información sobre reservas y menús degustación en Nexus Lounge.';

/** Email de contacto para consultas desde la web */
window.RESTAURANT_CONTACT_EMAIL = 'alobo@nexusfinlabs.com';

/**
 * URL del backend FastAPI.
 * En desarrollo: http://localhost:8090
 * En producción (TSC): https://tu-dominio/restaurants-api
 */
window.RESTAURANT_API_URL = 'http://localhost:8090';

/**
 * Stripe Payment Link para garantía de reserva (no-show).
 * Si está vacío, el modal ofrece copiar el resumen y contactar por WhatsApp.
 * Ejemplo: https://buy.stripe.com/test_eVq8wPbkPf9RaEP2eI7N600
 */
window.STRIPE_BOOKING_URL = 'https://buy.stripe.com/test_eVq8wPbkPf9RaEP2eI7N600';
