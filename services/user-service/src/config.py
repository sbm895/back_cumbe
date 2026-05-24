from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_url: str
    mongo_db: str = "users_db"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    eventos_url: str = "https://back-cumbe-events.onrender.com"

    class Config:
        env_file = ".env"


settings = Settings()
