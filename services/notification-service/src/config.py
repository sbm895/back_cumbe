from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_url: str
    mongo_db: str = "users_db"
    firebase_credentials_path: str = "firebase-credentials.json"
    eventos_url: str = "http://eventos-service:4003"
    usuarios_url: str = "http://user-service:4001"
    
    class Config:
        env_file = ".env"


settings = Settings()
