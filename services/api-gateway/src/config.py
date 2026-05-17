from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    user_service_url: str = "http://user-service:4001"

    class Config:
        env_file = ".env"


settings = Settings()
