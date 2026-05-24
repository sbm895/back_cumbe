from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_url: str
    mongo_db: str

    EVENT_SERVICE_URL: str = "https://back-cumbe-events.onrender.com/events/"

    class Config:
        env_file = ".env"

settings = Settings()