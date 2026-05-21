import httpx
from .config import settings


EPAYCO_BASE_URL = "https://secure.epayco.co"


async def create_pse_transaction(
    amount: float,
    user_email: str,
    event_name: str,
    bank_code: str,
    reference: str,
) -> dict:
    """
    Inicia una transacción PSE en ePayco.
    Retorna la URL de redirección al banco y la referencia.
    
    Patrón async: usa httpx.AsyncClient para no bloquear el event loop.
    """
    payload = {
        "bank": bank_code,
        "invoice": reference,
        "description": f"Entrada: {event_name}",
        "value": str(amount),
        "tax": "0",
        "tax_base": "0",
        "currency": "COP",
        "type_person": "0",          # 0=persona natural, 1=jurídica
        "doc_type": "CC",
        "user_email": user_email,
        "url_response": settings.payment_response_url,
        "url_confirmation": settings.payment_callback_url,
        "extra1": reference,
        "test": "1" if settings.epayco_test else "0",
    }

    auth_header = {
        "Authorization": f"Bearer {settings.epayco_p_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        response = await client.post(
            f"{EPAYCO_BASE_URL}/payment/process/pse",
            json=payload,
            headers=auth_header,
        )
        response.raise_for_status()
        return response.json()


async def get_transaction_status(epayco_ref: str) -> dict:
    """
    Consulta el estado actual de una transacción por su referencia.
    Usado en el webhook de confirmación y en polling de estado.
    """
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        response = await client.get(
            f"{EPAYCO_BASE_URL}/payment/process/id/{epayco_ref}",
            headers={"Authorization": f"Bearer {settings.epayco_p_key}"},
        )
        response.raise_for_status()
        return response.json()
