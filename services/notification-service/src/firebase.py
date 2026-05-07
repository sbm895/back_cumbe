import firebase_admin
from firebase_admin import credentials, messaging
from .config import settings

cred = credentials.Certificate(settings.firebase_credentials_path)
firebase_admin.initialize_app(cred)


async def send_push(token: str, title: str, body: str, data: dict = {}):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        token=token,
    )
    messaging.send(message)