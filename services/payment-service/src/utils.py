import jwt
import qrcode
from datetime import datetime, timedelta, timezone
from io import BytesIO
import base64
from .config import settings


def generar_token_pago(usuario_id: str, evento_id: str) -> str:
    """
    Genera un JWT token con usuario_id, evento_id y expiración.
    Token expira en JWT_EXPIRATION_HOURS (por defecto 48h).
    """
    payload = {
        "usuario_id": usuario_id,
        "evento_id": evento_id,
        "tipo": "confirmacion_pago",
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def generar_qr_base64(token: str) -> str:
    """
    Genera un QR a partir del token JWT y retorna la imagen como base64 PNG.
    """
    qr = qrcode.make(token)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


def validar_token_pago(token: str) -> dict:
    """
    Valida un JWT token de confirmación de pago.
    Retorna el payload si es válido, lanza excepción si está expirado o es inválido.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("QR expirado")
    except jwt.InvalidTokenError:
        raise ValueError("QR inválido")
