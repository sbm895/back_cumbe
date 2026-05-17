from contextlib import asynccontextmanager
from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

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
    yield
    client.close()


app = FastAPI(
    title="Event Service",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
app.include_router(router, prefix="/events")


@app.get("/health")
def health():
    return {"status": "ok", "service": "event-service"}
