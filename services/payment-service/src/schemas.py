from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .models import PaymentStatus


class InitiatePaymentRequest(BaseModel):
    """Payload para iniciar un pago PSE."""
    user_id: str
    event_id: str
    bank_code: str          # Código PSE del banco del usuario


class PaymentResponse(BaseModel):
    """Respuesta con estado de un pago."""
    id: str
    user_id: str
    event_id: str
    event_name: str
    amount: float
    currency: str
    status: PaymentStatus
    payment_url: Optional[str] = None
    epayco_ref: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None


class PSECallbackPayload(BaseModel):
    """Payload recibido en el webhook de confirmación de ePayco."""
    x_ref_payco: str                # ID interno de ePayco
    x_transaction_id: str           # ID de transacción en PSE
    x_response: str                 # "Aceptada", "Rechazada", "Pendiente"
    x_extra1: str                   # Nuestra referencia interna
    x_amount: str
    x_currency_code: str


class BankListResponse(BaseModel):
    """Lista de bancos disponibles para PSE."""
    bankCode: str
    bankName: str
