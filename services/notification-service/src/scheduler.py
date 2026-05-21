from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .clients import get_incoming_events, get_attendees_event, get_users_batch
from .firebase import send_push

scheduler = AsyncIOScheduler()
@scheduler.scheduled_job("interval", hours=1)
async def enviar_recordatorios():
    eventos = await get_incoming_events()
    for evento in eventos:
        asistentes_ids = await get_attendees_event(evento["id"])
        usuarios = await get_users_batch(asistentes_ids)
        for usuario in usuarios:
            if usuario.get("fcm_token"):
                await send_push(
                    token=usuario["fcm_token"],
                    title="Recordatorio",
                    body=f"{evento['name']} es mañana",
                    data={"evento_id": evento["id"]}
                )