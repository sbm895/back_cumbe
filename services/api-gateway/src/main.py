from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
import httpx

from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient()
    yield
    await app.state.client.aclose()


app = FastAPI(
    title="API Gateway",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}


@app.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_users(path: str, request: Request):
    url = f"{settings.user_service_url}/users/{path}"
    return await _proxy(request, url)


async def _proxy(request: Request, url: str):
    client: httpx.AsyncClient = request.app.state.client
    try:
        response = await client.request(
            method=request.method,
            url=url,
            content=await request.body(),
            headers=dict(request.headers),
        )
        return response.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Service unavailable")
