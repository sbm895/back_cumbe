from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB (igual que los demás servicios)
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str  = "users_db"

    # URLs internas de servicios (para enriquecer datos del pago)
    user_service_url: str  = "http://user-service:4001"
    event_service_url: str = "http://event-service:4003"

    # ePayco / PSE
    epayco_p_cust_id: str = ""       # Customer ID de ePayco
    epayco_p_key: str = ""           # Private Key de ePayco
    epayco_public_key: str = ""      # Public Key de ePayco
    epayco_test: bool = True         # True = sandbox, False = producción
    payment_callback_url: str = "http://localhost:3000/payments/callback"
    payment_response_url: str = "http://localhost:3000/payments/response"

    class Config:
        env_file = ".env"


settings = Settings()
