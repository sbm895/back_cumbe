from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    user_service_url: str = "http://user-service:4001"
    product_service_url: str = "http://product-service:4002"

    class Config:
        env_file = ".env"


settings = Settings()
