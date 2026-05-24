from contextlib import asynccontextmanager
from fastapi import FastAPI

from .scheduler import scheduler
from .routes import router
from .email_sender import email_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conectar cliente de email antes de iniciar scheduler
    await email_client.connect()
    scheduler.start()
    yield
    scheduler.shutdown()
    await email_client.close()


app = FastAPI(
    title="Notification Service",
    description="Servicio encargado de enviar notificaciones push y correos electrónicos a los usuarios."
                "Incluye endpoints para envío directo y orquestado en paralelo.",
    version="1.0.0",
    contact={"name": "Cumbe Team", "email": "devops@cumbe.com"},
    license_info={"name": "MIT"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
app.include_router(router, prefix="/notifications")


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification-service"}

