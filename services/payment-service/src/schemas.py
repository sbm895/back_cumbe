from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .models import PaymentStatus


class InitiatePaymentRequest(BaseModel):
    """Solicitud para iniciar un pago manual.
    
    El usuario y evento deben existir en sus respectivos microservicios.
    El evento debe tener un precio asociado.
    """
    user_id: str = Field(..., description="ID del usuario desde user-service", example="507f1f77bcf86cd799439011")
    event_id: str = Field(..., description="ID del evento desde event-service", example="507f1f77bcf86cd799439012")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "event_id": "507f1f77bcf86cd799439012",
            }
        }


class PaymentResponse(BaseModel):
    """Respuesta con detalles completos de un pago.
    
    Incluye información del usuario, evento, monto, estado y QR en base64.
    """
    id: str = Field(..., description="ID único del pago (MongoDB ObjectId)", example="507f1f77bcf86cd799439013")
    user_id: str = Field(..., description="ID del usuario", example="507f1f77bcf86cd799439011")
    event_id: str = Field(..., description="ID del evento", example="507f1f77bcf86cd799439012")
    user_email: str = Field(..., description="Email del usuario para notificaciones", example="user@example.com")
    event_name: str = Field(..., description="Nombre del evento", example="Concierto de Rock 2026")
    amount: float = Field(..., description="Monto en COP", example=50000.0)
    currency: str = Field(default="COP", description="Moneda (siempre COP)", example="COP")
    status: str = Field(..., description="Estado del pago: PENDING, COMPLETED, o FAILED", example="PENDING")
    qr_code_base64: Optional[str] = Field(None, description="QR code en PNG codificado en base64")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación del pago")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    confirmed_at: Optional[datetime] = Field(None, description="Fecha de confirmación (si está completado)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439013",
                "user_id": "507f1f77bcf86cd799439011",
                "event_id": "507f1f77bcf86cd799439012",
                "user_email": "user@example.com",
                "event_name": "Concierto de Rock 2026",
                "amount": 50000.0,
                "currency": "COP",
                "status": "COMPLETED",
                "created_at": "2026-05-23T10:30:00Z",
                "updated_at": "2026-05-23T10:35:00Z",
                "confirmed_at": "2026-05-23T10:35:00Z",
            }
        }


class PaymentWithQRResponse(BaseModel):
    """Respuesta de iniciación con QR codificado en base64.
    
    Contiene el código QR PNG en base64 listo para mostrar en UI.
    El token JWT está disponible para debugging.
    """
    payment_id: str = Field(..., description="ID del pago creado", example="507f1f77bcf86cd799439013")
    amount: float = Field(..., description="Monto en COP", example=50000.0)
    event_name: str = Field(..., description="Nombre del evento", example="Concierto de Rock 2026")
    qr_code_base64: str = Field(..., description="Imagen QR en PNG codificada como base64 (data:image/png;base64,...)")
    qr_token: str = Field(..., description="JWT token utilizado para generar el QR (para debugging)")
    status: str = Field(default="PENDING", description="Estado inicial del pago", example="PENDING")

    class Config:
        json_schema_extra = {
            "example": {
                "payment_id": "507f1f77bcf86cd799439013",
                "amount": 50000.0,
                "event_name": "Concierto de Rock 2026",
                "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "qr_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c3VhcmlvX2lkIjoiNTA3ZjFmNzdiY2Y4NmNkNzk5NDM5MDExIiwiZXZlbnRvX2lkIjoiNTA3ZjFmNzdiY2Y4NmNkNzk5NDM5MDEyIn0.signature",
                "status": "PENDING",
            }
        }


class ValidateQRRequest(BaseModel):
    """Solicitud para validar un QR y confirmar el pago.
    
    El token es el JWT generado al iniciar el pago,
    extraído del código QR escaneado.
    """
    token: str = Field(..., description="JWT token extraído del QR escaneado")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c3VhcmlvX2lkIjoiNTA3ZjFmNzdiY2Y4NmNkNzk5NDM5MDExIiwiZXZlbnRvX2lkIjoiNTA3ZjFmNzdiY2Y4NmNkNzk5NDM5MDEyIiwidGlwbyI6ImNvbmZpcm1hY2lvbl9wYWdvIiwiZXhwIjoxNzE5MTI3MDAwfQ.signature",
            }
        }


class ValidateQRResponse(BaseModel):
    """Respuesta de validación de QR.
    
    Confirma que el pago fue procesado exitosamente.
    """
    message: str = Field(..., description="Mensaje de confirmación", example="Pago confirmado exitosamente")
    event_id: str = Field(..., description="ID del evento", example="507f1f77bcf86cd799439012")
    user_id: str = Field(..., description="ID del usuario", example="507f1f77bcf86cd799439011")
    payment_id: Optional[str] = Field(None, description="ID del pago confirmado", example="507f1f77bcf86cd799439013")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Pago confirmado exitosamente",
                "event_id": "507f1f77bcf86cd799439012",
                "user_id": "507f1f77bcf86cd799439011",
                "payment_id": "507f1f77bcf86cd799439013",
            }
        }
