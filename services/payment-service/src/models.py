from typing import Optional
from beanie import Document
from pydantic import Field
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING    = "pending"     # Iniciado, esperando redirección PSE
    PROCESSING = "processing"  # Redirigido a PSE, esperando confirmación
    COMPLETED  = "completed"   # Confirmado exitosamente por PSE
    FAILED     = "failed"      # Rechazado por PSE o banco
    REFUNDED   = "refunded"    # Reembolso ejecutado


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

    # Integración PSE / ePayco
    epayco_ref: Optional[str] = None        # Referencia interna de ePayco
    epayco_transaction_id: Optional[str] = None  # ID de transacción de PSE
    payment_url: Optional[str] = None       # URL de redirección a PSE
    bank_code: Optional[str] = None         # Código del banco seleccionado por el usuario

    # Auditoría
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None

    class Settings:
        name = "payments"
        indexes = [
            [("user_id", 1)],           # Consultar pagos por usuario
            [("event_id", 1)],          # Consultar pagos por evento
            [("status", 1)],            # Filtrar por estado
            [("epayco_ref", 1)],        # Búsqueda por referencia PSE (webhook)
            [("created_at", -1)],       # Ordenar por fecha descendente
        ]
