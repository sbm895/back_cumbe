from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    user_service_url: str = "http://user-service:4001"
    event_service_url: str = "http://event-service:4003"
    notification_service_url: str = "http://notification-service:4004"
    payment_service_url: str = "http://payment-service:4005"

    class Config:
        env_file = ".env"


settings = Settings()
