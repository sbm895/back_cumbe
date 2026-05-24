import resend
from .config import settings
import logging

logger = logging.getLogger(__name__)


class EmailClient:
    def __init__(self):
        self._ready = False

    async def connect(self):
        if not settings.resend_api_key:
            logger.warning("[EMAIL] RESEND_API_KEY not set, emails will be mocked")
            return
        resend.api_key = settings.resend_api_key
        self._ready = True
        logger.info("[EMAIL] Resend client initialized")

    async def send(self, to_email: str, subject: str, html_body: str):
        if not self._ready:
            logger.info(f"[MOCK EMAIL] To: '{to_email}' | Subject: '{subject}'")
            return
        try:
            resend.Emails.send({
                "from": "Cumbe <onboarding@resend.dev>",
                "to": to_email,
                "subject": subject,
                "html": html_body,
            })
            logger.info(f"[EMAIL] Sent to {to_email}")
        except Exception as e:
            logger.error(f"[EMAIL] Failed to send to {to_email}: {e}")

    async def close(self):
        pass


email_client = EmailClient()


async def send_email(to_email: str, subject: str, html_body: str):
    await email_client.send(to_email, subject, html_body)