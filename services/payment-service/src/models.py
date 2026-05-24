from typing import Optional
from beanie import Document
from pydantic import Field
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING    = "pending"     # Iniciado, esperando confirmación manual
    COMPLETED  = "completed"   # Confirmado por escaneo de QR
    FAILED     = "failed"      # Cancelado o rechazado


class Payment(Document):
    # Referencias a otros servicios
    user_id: str
    event_id: str

    # Campos desnormalizados (Extended Reference Pattern)
    user_email: str             # Cacheado desde user-service para evitar lookups
    event_name: str             # Cacheado desde event-service para evitar lookups

    # Datos del pago
    amount: float               # En COP (pesos colombianos)
    currency: str = "COP"
    status: PaymentStatus = PaymentStatus.PENDING

    # JWT y QR Code para confirmación manual
    qr_token: str               # JWT token con usuario_id, evento_id, exp
    qr_code_base64: str         # PNG codificado en base64 para mostrar en UI/email

    # Auditoría
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None

    class Settings:
        name = "payments"
        indexes = [
            [("user_id", 1)],
            [("event_id", 1)],
            [("status", 1)],
            [("qr_token", 1)],          # Para validación rápida del QR
            [("created_at", -1)],
        ]
