from contextlib import asynccontextmanager
from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .config import settings
from .models import Payment
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(settings.mongo_url)
    await init_beanie(
        database=client[settings.mongo_db],
        document_models=[Payment],
    )
    yield
    client.close()


tags_metadata = [
    {
        "name": "Payments",
        "description": "Operaciones de pago con QR basado en JWT. Flujo: usuario inicia pago → recibe QR por email → muestra al organizador → organizador valida QR.",
    },
]

app = FastAPI(
    title="Payment Service - Cumbe",
    description="Servicio de pagos con validación manual mediante códigos QR. Genera tokens JWT "
                "que se codifican como QR PNG en base64. El usuario recibe el QR por email "
                "y lo muestra al organizador quien lo escanea para confirmar el pago.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)
app.include_router(router, prefix="/payments")


@app.get("/health", tags=["Health"])
def health():
    """Estado del servicio de pagos."""
    return {"status": "ok", "service": "payment-service", "version": "1.0.0"}
