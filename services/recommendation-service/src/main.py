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
    try:
        await init_beanie(
            database=client[settings.mongo_db],
            document_models=[User, Event],
        )
    except Exception as e:
        # No queremos bloquear la generación de OpenAPI si la BD no está disponible
        import logging
        logging.exception("init_beanie fallo durante el startup: %s", e)
    yield
    try:
        client.close()
    except Exception:
        pass


app = FastAPI(
    title="Recommendation Service",
    description=(
        "Servicio de recomendaciones híbridas para Cumbe. "
        "Combina filtrado por contenido (log-scaling), bono por usuarios seguidos y similitud de perfiles (coseno)."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={"name": "Cumbe Team", "email": "dev@example.com"},
)

app.include_router(router, prefix="/recs")


@app.get("/health")
def health():
    return {"status": "ok", "service": "recommendation-service"}