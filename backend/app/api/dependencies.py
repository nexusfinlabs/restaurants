from functools import lru_cache

from app.adapters.whatsapp_mock import WhatsAppMockAdapter
from app.repositories.db import ReservationRepository
from app.services.email_service import EmailService
from app.services.llm_service import LLMService
from app.services.payment_service import PaymentService
from app.services.reservation_service import ReservationService


@lru_cache
def get_repo() -> ReservationRepository:
    return ReservationRepository()


@lru_cache
def get_reservation_service() -> ReservationService:
    return ReservationService(get_repo())


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()


@lru_cache
def get_whatsapp_adapter() -> WhatsAppMockAdapter:
    return WhatsAppMockAdapter(get_reservation_service(), get_llm_service())


@lru_cache
def get_payment_service() -> PaymentService:
    return PaymentService()


@lru_cache
def get_email_service() -> EmailService:
    return EmailService(get_repo(), get_reservation_service(), get_llm_service())
