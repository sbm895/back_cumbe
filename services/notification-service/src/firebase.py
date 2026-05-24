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
        print(f"[MOCK PUSH] Sent to Token: '{token}' | Title: '{title}' | Body: '{body}' | Data: {data}")
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        token=token,
    )
    messaging.send(message)


async def send_multicast_push(tokens: list[str], title: str, body: str, data: dict = {}):
    app = _get_firebase_app()
    if app is None:
        print(f"[MOCK MULTICAST PUSH] Sent to {len(tokens)} tokens: {tokens} | Title: '{title}' | Body: '{body}' | Data: {data}")
        return None

    responses = []
    # Firebase limits multicast messages to 500 tokens per call
    for i in range(0, len(tokens), 500):
        chunk = tokens[i:i + 500]
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data,
            tokens=chunk,
        )
        batch_response = messaging.send_each_for_multicast(message)
        responses.append(batch_response)
    return responses