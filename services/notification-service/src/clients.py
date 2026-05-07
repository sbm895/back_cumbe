import httpx
from .config import settings


async def get_eventos_proximos() -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.eventos_url}/eventos/proximos")
        response.raise_for_status()
        return response.json()


async def get_asistentes_evento(evento_id: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.eventos_url}/eventos/{evento_id}/asistentes")
        response.raise_for_status()
        return response.json()


async def get_usuarios_batch(ids: list[str]) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.usuarios_url}/usuarios/batch",
            json={"ids": ids}
        )
        response.raise_for_status()
        return response.json()