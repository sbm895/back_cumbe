from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_url: str
    mongo_db: str = "users_db"
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
