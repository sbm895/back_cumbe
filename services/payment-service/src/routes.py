import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
import httpx

from .models import Payment, PaymentStatus
from .schemas import InitiatePaymentRequest, PaymentResponse, PSECallbackPayload
from .epayco_client import create_pse_transaction, get_transaction_status
from .config import settings

router = APIRouter()


# ── Bancos disponibles ──────────────────────────────────────────────────────

@router.get("/banks", summary="Listar bancos PSE disponibles")
async def list_banks():
    """Retorna los bancos habilitados para pago PSE."""
    # Lista estática representativa; en producción se consulta a ePayco
    return [
        {"bankCode": "1007", "bankName": "Bancolombia"},
        {"bankCode": "1032", "bankName": "Banco Caja Social"},
        {"bankCode": "1040", "bankName": "Banco Agrario"},
        {"bankCode": "1052", "bankName": "Banco AV Villas"},
        {"bankCode": "1013", "bankName": "BBVA Colombia"},
        {"bankCode": "1023", "bankName": "Banco de Occidente"},
        {"bankCode": "1006", "bankName": "Banco Itaú"},
        {"bankCode": "1062", "bankName": "Banco Falabella"},
    ]


# ── Iniciar pago ────────────────────────────────────────────────────────────

@router.post("/initiate", response_model=PaymentResponse, status_code=201,
             summary="Iniciar transacción PSE")
async def initiate_payment(body: InitiatePaymentRequest):
    """
    1. Verifica el usuario y el evento consultando sus microservicios.
    2. Crea un registro de pago con estado PENDING en MongoDB.
    3. Solicita a ePayco la URL de redirección PSE.
    4. Actualiza el pago con la URL y retorna al cliente.
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

    reference = str(uuid.uuid4())

    # Persistir pago en estado PENDING
    payment = Payment(
        user_id=body.user_id,
        event_id=body.event_id,
        user_email=user["email"],
        event_name=event["name"],
        amount=amount,
        bank_code=body.bank_code,
        status=PaymentStatus.PENDING,
    )
    await payment.insert()

    # Solicitar URL PSE a ePayco
    try:
        epayco_data = await create_pse_transaction(
            amount=amount,
            user_email=user["email"],
            event_name=event["name"],
            bank_code=body.bank_code,
            reference=reference,
        )
    except httpx.HTTPError as e:
        await payment.delete()
        raise HTTPException(status_code=502, detail=f"Payment gateway error: {str(e)}")

    # Actualizar pago con datos de ePayco
    payment.epayco_ref = epayco_data.get("data", {}).get("ref_payco")
    payment.payment_url = epayco_data.get("data", {}).get("urlbanco")
    payment.status = PaymentStatus.PROCESSING
    payment.updated_at = datetime.utcnow()
    await payment.save()

    return PaymentResponse(
        id=str(payment.id),
        **payment.model_dump(exclude={"id"})
    )


# ── Webhook de confirmación (callback ePayco) ───────────────────────────────

@router.post("/callback", summary="Webhook de confirmación PSE")
async def payment_callback(payload: PSECallbackPayload, background_tasks: BackgroundTasks):
    """
    Endpoint que ePayco llama con el resultado final de la transacción.
    Se actualiza el estado del pago y, si fue exitoso, se dispara
    una notificación de confirmación en background.
    """
    payment = await Payment.find_one(Payment.epayco_ref == payload.x_ref_payco)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    status_map = {
        "Aceptada": PaymentStatus.COMPLETED,
        "Rechazada": PaymentStatus.FAILED,
        "Pendiente": PaymentStatus.PROCESSING,
    }
    payment.status = status_map.get(payload.x_response, PaymentStatus.FAILED)
    payment.epayco_transaction_id = payload.x_transaction_id
    payment.updated_at = datetime.utcnow()

    if payment.status == PaymentStatus.COMPLETED:
        payment.confirmed_at = datetime.utcnow()
        background_tasks.add_task(_notify_payment_success, payment)

    await payment.save()
    return {"received": True}


async def _notify_payment_success(payment: Payment):
    """
    Background task: llama al notification-service para enviar push
    de confirmación de pago al usuario.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Obtener fcm_token del usuario
        user_resp = await client.get(
            f"{settings.user_service_url}/users/{payment.user_id}"
        )
        if user_resp.status_code != 200:
            return
        user = user_resp.json()
        fcm_token = user.get("fcm_token")
        if not fcm_token:
            return

        await client.post(
            f"http://notification-service:4004/notifications/send-direct",
            json={
                "token": fcm_token,
                "title": "✅ Pago confirmado",
                "body": f"Tu entrada para '{payment.event_name}' fue procesada exitosamente.",
                "data": {"event_id": payment.event_id, "payment_id": str(payment.id)},
            },
        )


# ── Consultas ───────────────────────────────────────────────────────────────

@router.get("/{payment_id}", response_model=PaymentResponse,
            summary="Obtener pago por ID")
async def get_payment(payment_id: str):
    payment = await Payment.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/user/{user_id}", response_model=list[PaymentResponse],
            summary="Historial de pagos de un usuario")
async def get_user_payments(user_id: str):
    return await Payment.find(Payment.user_id == user_id).sort(-Payment.created_at).to_list()


@router.get("/event/{event_id}", response_model=list[PaymentResponse],
            summary="Pagos asociados a un evento")
async def get_event_payments(event_id: str):
    return await Payment.find(Payment.event_id == event_id).to_list()


@router.get("/{payment_id}/status", summary="Consultar estado actualizado desde PSE")
async def refresh_payment_status(payment_id: str):
    """
    Consulta el estado directamente en ePayco (útil para polling del cliente
    mientras el usuario completa el flujo en el banco).
    """
    payment = await Payment.get(payment_id)
    if not payment or not payment.epayco_ref:
        raise HTTPException(status_code=404, detail="Payment not found or not initiated")

    try:
        epayco_status = await get_transaction_status(payment.epayco_ref)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not reach payment gateway")

    return {
        "payment_id": payment_id,
        "local_status": payment.status,
        "gateway_status": epayco_status,
    }
