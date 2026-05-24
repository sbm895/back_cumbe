from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB (igual que los demás servicios)
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str  = "users_db"

    # URLs internas de servicios (para enriquecer datos del pago)
    user_service_url: str  = "http://user-service:4001"
    event_service_url: str = "http://event-service:4003"
    notification_service_url: str = "http://notification-service:4004"

    # JWT para tokens de confirmación de pago
    jwt_secret_key: str = "your-secret-key-change-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 48

    class Config:
        env_file = ".env"


settings = Settings()
