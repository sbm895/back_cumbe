import os
import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin import get_app, initialize_app
from .config import settings


def _get_firebase_app():
    try:
        return get_app()
    except ValueError:
        if not settings.firebase_credentials_path:
            return None
        if not os.path.exists(settings.firebase_credentials_path):
            return None
        cred = credentials.Certificate(settings.firebase_credentials_path)
        return initialize_app(cred)


async def send_push(token: str, title: str, body: str, data: dict = {}):
    app = _get_firebase_app()
    if app is None:
        raise RuntimeError(
            "Firebase credentials are not configured or the credentials file was not found."
        )

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        token=token,
    )
    messaging.send(message)