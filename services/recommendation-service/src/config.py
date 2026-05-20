from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_url: str
    mongo_db: str

    class Config:
        env_file = ".env"

settings = Settings()