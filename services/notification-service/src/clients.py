import httpx
from .config import settings


async def get_incoming_events() -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.eventos_url}/events/incoming")
        response.raise_for_status()
        return response.json()


async def get_attendees_event(event_id: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.eventos_url}/events/{event_id}/attendees")
        response.raise_for_status()
        return response.json()


async def get_users_batch(ids: list[str]) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.usuarios_url}/users/batch",
            json={"ids": ids}
        )
        response.raise_for_status()
        return response.json()