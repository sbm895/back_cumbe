from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from .config import settings


class EmailClient:
    def __init__(self):
        self._fm = None

    async def connect(self):
        """Initialize FastMail connection if SMTP is configured."""
        print(f"[EMAIL DEBUG] host={settings.smtp_host}, port={settings.smtp_port}")
        print(f"[EMAIL DEBUG] user={settings.smtp_username}")
        print(f"[EMAIL DEBUG] use_tls={settings.smtp_use_tls!r} (type: {type(settings.smtp_use_tls)})")
        print(f"[EMAIL DEBUG] password length={len(settings.smtp_password) if settings.smtp_password else 0}")
        if not settings.smtp_host:
            return
        try:
            config = ConnectionConfig(
                MAIL_USERNAME=settings.smtp_username,
                MAIL_PASSWORD=settings.smtp_password,
                MAIL_FROM=settings.smtp_sender,
                MAIL_PORT=settings.smtp_port,
                MAIL_SERVER=settings.smtp_host,
                MAIL_FROM_NAME="Cumbe Notifications",
                MAIL_STARTTLS=settings.smtp_use_tls,
                MAIL_SSL_TLS=False,  # Use STARTTLS instead of SSL
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True,
            )
            self._fm = FastMail(config)
        except Exception as e:
            print(f"[EMAIL] Failed to initialize FastMail: {e}")

    async def send(self, to_email: str, subject: str, html_body: str):
        """Send email via FastMail or print mock if not configured."""
        if not settings.smtp_host:
            print(f"[MOCK EMAIL] Sent to: '{to_email}' | Subject: '{subject}' | HTML Body: '{html_body[:100]}...'")
            return

        if self._fm is None:
            print(f"[EMAIL] FastMail not initialized, skipping send to {to_email}")
            return

        try:
            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=html_body,
                subtype="html",
            )
            await self._fm.send_message(message)
        except Exception as e:
            print(f"[EMAIL] Failed to send to {to_email}: {e}")

    async def close(self):
        """Close connection (FastMail handles this internally)."""
        pass


email_client = EmailClient()


async def send_email(to_email: str, subject: str, html_body: str):
    """Public function to send email."""
    await email_client.send(to_email, subject, html_body)
