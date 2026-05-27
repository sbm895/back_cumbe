from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import httpx

from .auth import require_publisher
from .models import Payment, PaymentStatus
from .schemas import (
    InitiatePaymentRequest,
    PaymentResponse,
    PaymentWithQRResponse,
    ValidateQRRequest,
    ValidateQRResponse,
)
from .utils import generar_token_pago, generar_qr_base64, validar_token_pago
from .config import settings

router = APIRouter(tags=["Payments"])


# ── Iniciar pago y generar QR ──────────────────────────────────────────────

@router.post(
    "/initiate",
    response_model=PaymentWithQRResponse,
    status_code=201,
    summary="Iniciar pago manual y generar QR",
    description="Crea un nuevo registro de pago, genera un JWT token y QR code, y envía una notificación al usuario con el código QR embebido en email.",
    responses={
        201: {"description": "Pago iniciado exitosamente con QR generado"},
        404: {"description": "Usuario o evento no encontrado"},
        400: {"description": "Evento sin precio asociado"},
    },
)
async def initiate_payment(body: InitiatePaymentRequest, background_tasks: BackgroundTasks):
    """
    ## Flujo de pago manual con QR

    1. Verifica el usuario y evento consultando microservicios
    2. Crea un documento de pago en estado PENDING
    3. Genera JWT token (expira en 48 horas)
    4. Codifica token como QR PNG (base64)
    5. Envía email con QR embebido + push FCM
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Verificar usuario
        user_resp = await client.get(
            f"{settings.user_service_url}/users/{body.user_id}"
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        user = user_resp.json()

        # Verificar evento y obtener precio
        event_resp = await client.get(
            f"{settings.event_service_url}/events/{body.event_id}"
        )
        if event_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Event not found")
        event = event_resp.json()

    amount = float(event.get("price", 0))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Event has no associated price")

    # Generar JWT token y QR
    qr_token = generar_token_pago(body.user_id, body.event_id)
    qr_code_base64 = generar_qr_base64(qr_token)

    # Crear registro de pago
    payment = Payment(
        user_id=body.user_id,
        event_id=body.event_id,
        user_email=user.get("email", ""),
        event_name=event.get("name", ""),
        amount=amount,
        status=PaymentStatus.PENDING,
        qr_token=qr_token,
        qr_code_base64=qr_code_base64,
    )
    await payment.insert()

    # Enviar notificación en background
    background_tasks.add_task(_notify_payment_initiated, payment, user)

    return PaymentWithQRResponse(
        payment_id=str(payment.id),
        amount=amount,
        event_name=event.get("name", ""),
        qr_code_base64=qr_code_base64,
        qr_token=qr_token,
        status=payment.status.value,
    )


# ── Validar QR (escaneo por app/web) ────────────────────────────────────────────────

@router.post(
    "/validate",
    response_model=ValidateQRResponse,
    status_code=200,
    summary="Validar QR y confirmar pago",
    description="Valida el JWT token extraído del QR, marca el pago como COMPLETADO, y envía email de confirmación al usuario.",
    responses={
        200: {"description": "Pago confirmado exitosamente"},
        400: {"description": "Token inválido, expirado, o pago ya confirmado"},
        404: {"description": "Pago no encontrado"},
    },
)
async def validate_qr(body: ValidateQRRequest, background_tasks: BackgroundTasks):
    """
    ## Validación de QR y confirmación de pago

    Decodifica y valida el JWT token del QR:
    1. Extrae usuario_id y evento_id del token
    2. Busca pago en MongoDB por usuario + evento
    3. Valida que no esté ya confirmado
    4. Marca como COMPLETED y guarda timestamp
    5. Envía email de confirmación + push FCM
    """
    try:
        payload = validar_token_pago(body.token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    usuario_id = payload.get("usuario_id")
    evento_id = payload.get("evento_id")

    # Buscar el pago por usuario + evento
    payment = await Payment.find_one(
    Payment.user_id == usuario_id,
    Payment.event_id == evento_id
    )   
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == PaymentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Payment already confirmed")

    if payment.status == PaymentStatus.FAILED:
        raise HTTPException(status_code=400, detail="Payment was cancelled")

    # Marcar como completado
    payment.status = PaymentStatus.COMPLETED
    payment.confirmed_at = datetime.utcnow()
    payment.updated_at = datetime.utcnow()
    await payment.save()

    # Notificar en background
    background_tasks.add_task(_notify_payment_confirmed, payment)

    return ValidateQRResponse(
        message="Pago confirmado exitosamente",
        event_id=evento_id,
        user_id=usuario_id,
        payment_id=str(payment.id),
    )


# ── Background tasks (notificaciones) ────────────────────────────────────────────────

async def _notify_payment_initiated(payment: Payment, user: dict):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{settings.notification_service_url}/notifications/dispatch",
            json={
                "usuarios": [{
                    "id": payment.user_id,
                    "email": user.get("email"),
                    "fcm_token": user.get("fcm_token"),
                }],
                "title": "🧾 Pago pendiente",
                "body": f"Se ha iniciado un pago de ${payment.amount:,.0f} COP para '{payment.event_name}'. Escanea el QR para confirmar.",
                "data": {
                    "event_id": payment.event_id,
                    "payment_id": str(payment.id)
                },
            },
            timeout=10.0,
        )


async def _notify_payment_confirmed(payment: Payment):
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            f"{settings.user_service_url}/users/{payment.user_id}",
            timeout=10.0
        )
        if user_resp.status_code != 200:
            return
        user = user_resp.json()

        await client.post(
            f"{settings.notification_service_url}/notifications/dispatch",
            json={
                "usuarios": [{
                    "id": payment.user_id,
                    "email": user.get("email"),
                    "fcm_token": user.get("fcm_token"),
                }],
                "title": "✅ Entrada confirmada",
                "body": f"Tu pago de ${payment.amount:,.0f} COP para '{payment.event_name}' fue confirmado.",
                "data": {
                    "event_id": payment.event_id,
                    "payment_id": str(payment.id)
                },
            },
            timeout=10.0,
        )

# ── Consultas ───────────────────────────────────────────────────────────────

@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Obtener detalles de un pago por ID",
    description="Retorna los detalles completos de un pago, incluyendo estado, usuario, evento, monto y QR base64.",
    responses={
        200: {"description": "Pago encontrado"},
        404: {"description": "Pago no encontrado"},
    },
)
async def get_payment(payment_id: str):
    payment = await Payment.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse(
        id=str(payment.id),
        user_id=payment.user_id,
        event_id=payment.event_id,
        user_email=payment.user_email,
        event_name=payment.event_name,
        amount=payment.amount,
        status=payment.status.value,
        qr_code_base64=payment.qr_code_base64,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        confirmed_at=payment.confirmed_at,
    )


@router.get(
    "/user/{user_id}",
    response_model=list[PaymentResponse],
    summary="Obtener historial de pagos de un usuario",
    description="Retorna todos los pagos de un usuario, ordenados por fecha más reciente primero.",
    responses={
        200: {"description": "Lista de pagos del usuario (puede estar vacía)"},
    },
)
async def get_user_payments(user_id: str):
    payments = await Payment.find(Payment.user_id == user_id).sort(-Payment.created_at).to_list()
    return [
        PaymentResponse(
            id=str(p.id),
            user_id=p.user_id,
            event_id=p.event_id,
            user_email=p.user_email,
            event_name=p.event_name,
            amount=p.amount,
            status=p.status.value,
            qr_code_base64=p.qr_code_base64,
            created_at=p.created_at,
            updated_at=p.updated_at,
            confirmed_at=p.confirmed_at,
        )
        for p in payments
    ]


@router.get(
    "/event/{event_id}",
    response_model=list[PaymentResponse],
    summary="Obtener todos los pagos de un evento",
    description="Retorna todos los pagos confirmados/pendientes para un evento. Útil para que el organizador vea asistencia.",
    responses={
        200: {"description": "Lista de pagos del evento (puede estar vacía)"},
    },
)
async def get_event_payments(
    event_id: str,
    _publisher: dict[str, str] = Depends(require_publisher),
):
    payments = await Payment.find(Payment.event_id == event_id).to_list()
    return [
        PaymentResponse(
            id=str(p.id),
            user_id=p.user_id,
            event_id=p.event_id,
            user_email=p.user_email,
            event_name=p.event_name,
            amount=p.amount,
            status=p.status.value,
            qr_code_base64=p.qr_code_base64,
            created_at=p.created_at,
            updated_at=p.updated_at,
            confirmed_at=p.confirmed_at,
        )
        for p in payments
    ]


@router.post(
    "/{payment_id}/cancel",
    response_model=PaymentResponse,
    summary="Cancelar un pago",
    description="Cancela un pago pendiente marcándolo como FAILED. No se pueden cancelar pagos confirmados.",
    responses={
        200: {"description": "Pago cancelado exitosamente"},
        400: {"description": "No se puede cancelar un pago confirmado"},
        404: {"description": "Pago no encontrado"},
    },
)
async def cancel_payment(payment_id: str):
    payment = await Payment.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status == PaymentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel confirmed payment")
    
    payment.status = PaymentStatus.FAILED
    payment.updated_at = datetime.utcnow()
    await payment.save()
    
    return PaymentResponse(
        id=str(payment.id),
        user_id=payment.user_id,
        event_id=payment.event_id,
        user_email=payment.user_email,
        event_name=payment.event_name,
        amount=payment.amount,
        status=payment.status.value,
        qr_code_base64=payment.qr_code_base64,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        confirmed_at=payment.confirmed_at,
    )
