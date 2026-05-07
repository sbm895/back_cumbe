from typing import Optional
from beanie import Document
from pydantic import EmailStr


class User(Document):
    name: str
    email: EmailStr
    fcm_token: Optional[str] = None  # se actualiza cada login
    profile_picture: Optional[str] = None      # URL o path de la foto
    favorites: list[str] = []                   # IDs de eventos favoritos
    attended_events: list[str] = []             # IDs de eventos asistidos

    class Settings:
        name = "users"


class Event(Document): 
    name: str
    description: Optional[str] = None
    date: str
    picture: Optional[list[str]] = None      # URL o path de la foto
    location: Optional[str] = None
    organizer: User
    attendees: list[str] = []    # IDs de usuarios asistentes
    categories: list[str] = []   # Categorías del evento

    class Settings:
        name = "events"