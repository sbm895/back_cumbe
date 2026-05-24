from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .clients import get_incoming_events, get_attendees_event, get_users_batch
from .notifier import dispatch_notifications
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", hours=1)
async def enviar_recordatorios():
    now = datetime.now(ZoneInfo("America/Bogota"))
    logger.info(f"[SCHEDULER] Iniciando tarea de recordatorios a las {now.isoformat()}")
    reminder_min = timedelta(hours=23)
    reminder_max = timedelta(hours=24)

    logger.info(
        f"[SCHEDULER] Corriendo a {now.isoformat()}, buscando eventos con recordatorios entre "
        f"{reminder_min} y {reminder_max} desde ahora"
    )

    eventos = await get_incoming_events()
    logger.info(f"[SCHEDULER] {len(eventos)} eventos encontrados")

    for evento in eventos:
        # Normalizar id del evento: puede venir como 'id' o '_id' desde el servicio de eventos
        event_id = evento.get("id") or evento.get("_id")
        if "date" not in evento:
            continue
        try:
            date_str = evento["date"].replace("Z", "+00:00")
            event_date = datetime.fromisoformat(date_str)
            if event_date.tzinfo is None:
                event_date = event_date.replace(tzinfo=ZoneInfo("America/Bogota"))

            time_until_event = event_date - now
            if not (reminder_min <= time_until_event < reminder_max):
                logger.info(
                    f"[SCHEDULER] Evento '{evento.get('name', event_id)}' con fecha "
                    f"{event_date.isoformat()} está a {time_until_event.total_seconds() / 3600:.2f}h; "
                    "fuera de la ventana de recordatorio de 23-24h; saltando"
                )
                continue
        except Exception as exc:
            logger.warning(
                f"[SCHEDULER] No se pudo parsear la fecha del evento {event_id} "
                f"(date={evento.get('date')}): {exc}"
            )
            continue

        asistentes_ids = await get_attendees_event(event_id)
        if not asistentes_ids:
            logger.info(f"[SCHEDULER] Evento '{evento.get('name', event_id)}' no tiene asistentes; saltando")
            continue
            
        usuarios = await get_users_batch(asistentes_ids)
        if not usuarios:
            logger.info(f"[SCHEDULER] No se encontraron usuarios para asistentes de evento '{evento.get('name', event_id)}'; saltando")
            continue

        logger.info(f"[SCHEDULER] Notificando evento '{evento.get('name', event_id)}' a {len(usuarios)} usuarios")
        await dispatch_notifications(
            usuarios=usuarios,
            title="Recordatorio",
            body=f"⏰ ¡Recordatorio! '{evento.get('name', event_id)}' es mañana.",
            data={"evento_id": event_id}
        )