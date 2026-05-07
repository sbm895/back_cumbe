from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .clients import get_eventos_proximos, get_asistentes_evento, get_usuarios_batch
from .firebase import send_push

scheduler = AsyncIOScheduler()
@scheduler.scheduled_job("interval", hours=1)
async def enviar_recordatorios():
    eventos = await get_eventos_proximos()
    for evento in eventos:
        asistentes = await get_asistentes_evento(evento["id"])
        ids = [a["id"] for a in asistentes]
        usuarios = await get_usuarios_batch(ids)
        for usuario in usuarios:
            if usuario.get("fcm_token"):
                await send_push(
                    token=usuario["fcm_token"],
                    title="Recordatorio",
                    body=f"{evento['nombre']} es mañana",
                    data={"evento_id": evento["id"]}
                )