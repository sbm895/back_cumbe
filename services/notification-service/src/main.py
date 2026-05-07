from contextlib import asynccontextmanager
from fastapi import FastAPI
from .scheduler import scheduler
from .clients import get_eventos_proximos, get_usuario
from .firebase import send_push
from .config import settings
from .models import User, Event
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
app.include_router(router)


app = FastAPI(title="Notification Service", lifespan=lifespan)
app.include_router(router, prefix="/notifs")


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification-service"}
