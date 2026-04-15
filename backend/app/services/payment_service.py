from typing import Any, Dict, Optional

from app.config import settings


class PaymentService:
    def create_setup_intent(self, reservation_id: int, customer_email: Optional[str]) -> Dict[str, str]:
        if settings.stripe_secret_key:
            try:
                import stripe

                stripe.api_key = settings.stripe_secret_key
                customer = stripe.Customer.create(email=customer_email) if customer_email else None
                intent = stripe.SetupIntent.create(
                    customer=customer.id if customer else None,
                    payment_method_types=['card'],
                    usage='off_session',
                )
                return {
                    'setup_intent_id': intent.id,
                    'client_secret': intent.client_secret or '',
                    'provider': 'stripe',
                }
            except Exception:
                pass

        return {
            'setup_intent_id': f'set_mock_{reservation_id}',
            'client_secret': f'set_mock_{reservation_id}_secret',
            'provider': 'mock',
        }

    def attach_payment_method(self, payment_method_id: str) -> Dict[str, Any]:
        if settings.stripe_secret_key:
            try:
                import stripe

                stripe.api_key = settings.stripe_secret_key
                pm = stripe.PaymentMethod.retrieve(payment_method_id)
                card = pm.get('card') or {}
                return {
                    'payment_method_id': str(pm.get('id', payment_method_id)),
                    'brand': card.get('brand'),
                    'last4': card.get('last4'),
                    'exp_month': card.get('exp_month'),
                    'exp_year': card.get('exp_year'),
                }
            except Exception:
                pass

        return {
            'payment_method_id': payment_method_id,
            'brand': 'mock',
            'last4': '4242',
            'exp_month': 12,
            'exp_year': 2030,
        }
