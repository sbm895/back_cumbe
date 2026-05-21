from typing import Optional
from beanie import Document
from pydantic import EmailStr, field_validator
from datetime import datetime


class User(Document):
    name: str
    email: EmailStr
    fcm_token: Optional[str] = None  # se actualiza cada login
    profile_picture: Optional[str] = None      # URL o path de la foto
    favorites: list[str] = []                   # IDs de eventos favoritos
    attended_events: list[str] = []             # IDs de eventos asistidos
    following: list[str] = []

    class Settings:
        name = "users"


class Event(Document): 
    name: str
    description: Optional[str] = None
    date: datetime
    picture: Optional[list[str]] = None      # URL o path de la foto
    location: Optional[str] = None
    organizer: str
    attendees: list[str] = []    # IDs de usuarios asistentes
    categories: list[str] = []   # Categorías del evento
    
    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%d/%m/%Y %H:%M")
            except ValueError:
                raise ValueError("Formato de fecha inválido. Usa dd/mm/yyyy hh:mm")
        return v

    class Settings:
        name = "events"