from typing import Optional
from beanie import Document
from pydantic import EmailStr


class User(Document):
    name: str
    email: EmailStr
    hashed_password: Optional[str] = None
    fcm_token: Optional[str] = None  # se actualiza cada login
    profile_picture: Optional[str] = None      # URL o path de la foto
    favorites: list[str] = []                   # IDs de eventos favoritos
    attended_events: list[str] = []             # IDs de eventos asistidos

    class Settings:
        name = "users"