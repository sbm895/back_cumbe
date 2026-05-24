import asyncio
import logging
from .firebase import send_multicast_push
from .email_sender import send_email

logger = logging.getLogger(__name__)


async def dispatch_notifications(usuarios: list[dict], title: str, body: str, data: dict = {}):
    logger.info(f"[NOTIFIER] Starting dispatch_notifications for {len(usuarios)} users | Title: '{title}'")
    tasks = []

    # 1. Agrupar tokens FCM para envío multicast
    tokens = [u["fcm_token"] for u in usuarios if u.get("fcm_token")]
    if tokens:
        logger.info(f"[NOTIFIER] Collected {len(tokens)} FCM tokens for push notification")
        tasks.append(send_multicast_push(tokens, title, body, data))
    else:
        logger.debug("[NOTIFIER] No FCM tokens available for push notification")

    # 2. Agregar tareas de correo electrónico en paralelo
    email_count = 0
    for usuario in usuarios:
        if usuario.get("email"):
            email_count += 1
            logger.debug(f"[NOTIFIER] Queueing email to: {usuario['email']}")
            html_body = f"""
            <html>
                <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f9f9f9; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05); border: 1px solid #eef2f5;">
                        <h2 style="color: #D32F2F; font-size: 24px; font-weight: 600; margin-top: 0; margin-bottom: 20px; border-bottom: 2px solid #f0f3f6; padding-bottom: 15px;">
                            {title}
                        </h2>
                        <p style="font-size: 16px; color: #8B0000; margin-bottom: 30px;">
                            {body}
                        </p>
                        <div style="text-align: center; margin-bottom: 30px;">
                            <a style="background-color: #D32F2F; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 500; display: inline-block;">
                                Cumbe
                            </a>
                        </div>
                        <hr style="border: 0; border-top: 1px solid #f0f3f6; margin: 30px 0;">
                        <footer style="font-size: 12px; color: #9B9B9B; text-align: center; line-height: 1.4;">
                            Este es un correo automático enviado por Cumbe.<br>
                            Por favor no respondas directamente a este mensaje.<br>
                            © 2026 Cumbe. Todos los derechos reservados.
                        </footer>
                    </div>
                </body>
            </html>
            """
            tasks.append(send_email(usuario["email"], title, html_body))
    
    if email_count > 0:
        logger.info(f"[NOTIFIER] Queued {email_count} emails for sending")
    else:
        logger.debug("[NOTIFIER] No emails available for sending")

    # 3. Disparar todos los envíos (Push + Emails) concurrentemente sin bloquearse
    if tasks:
        logger.info(f"[NOTIFIER] Executing {len(tasks)} notification tasks concurrently")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[NOTIFIER] Task {i+1} failed with error: {str(result)}")
            else:
                logger.debug(f"[NOTIFIER] Task {i+1} completed successfully")
        
        logger.info(f"[NOTIFIER] dispatch_notifications completed for {len(usuarios)} users")
    else:
        logger.warning("[NOTIFIER] No notification tasks to execute (no FCM tokens or emails available)")
