from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_url: str
    mongo_db: str = "users_db"
    firebase_credentials_path: str = "firebase-credentials.json"
    eventos_url: str = "http://event-service:4003"
    usuarios_url: str = "http://user-service:4001"
    
    # SMTP Settings
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_sender: str = "noreply@cumbe.com"
    smtp_use_tls: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()
