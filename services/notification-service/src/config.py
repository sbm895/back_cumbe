from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_url: str
    mongo_db: str = "users_db"
    firebase_credentials_path: str = "firebase-credentials.json"
    eventos_url: str = "https://back-cumbe-events.onrender.com"
    usuarios_url: str = "https://back-cumbe-users.onrender.com"
    
    resend_api_key: str = ""
    
    class Config:
        env_file = ".env"


settings = Settings()
