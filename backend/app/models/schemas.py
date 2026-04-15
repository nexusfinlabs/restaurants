from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

ReservationStatus = Literal['pending_info', 'pending_payment_method', 'confirmed', 'cancelled', 'no_show']


class ReservationCreate(BaseModel):
    name: str = Field(min_length=2)
    phone: str = Field(min_length=6)
    email: Optional[EmailStr] = None
    date: str
    time: str
    party_size: int = Field(ge=1, le=20)
    source: str = 'whatsapp'
    notes: Optional[str] = None


class ConfirmReservationRequest(BaseModel):
    payment_method_id: Optional[str] = None


class WhatsAppInbound(BaseModel):
    user_id: str
    message: str


class MenuQuestionRequest(BaseModel):
    question: str


class MenuQuestionResponse(BaseModel):
    answer: str


class SetupIntentRequest(BaseModel):
    reservation_id: int
    customer_email: Optional[EmailStr] = None


class SetupIntentResponse(BaseModel):
    setup_intent_id: str
    client_secret: str
    provider: str
