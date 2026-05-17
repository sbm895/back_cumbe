from contextlib import asynccontextmanager
from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .scheduler import scheduler
from .clients import get_eventos_proximos
from .firebase import send_push
from .config import settings
from .models import User, Event
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(settings.mongo_url)
    await init_beanie(
        database=client[settings.mongo_db],
        document_models=[User, Event],
    )
    scheduler.start()
    yield
    scheduler.shutdown()
    client.close()


app = FastAPI(
    title="Notification Service",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
app.include_router(router, prefix="/notifs")


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification-service"}
