from typing import Optional
from beanie import Document
from pydantic import BaseModel, EmailStr, field_validator
from .categories import CategoriaBQ
from datetime import datetime


class EventReview(BaseModel):
    event_id: str
    review_text: str  # renaming to review_text avoids confusion with the parent list name

class User(Document):
    name: str
    email: EmailStr
    fcm_token: Optional[str] = None  # se actualiza cada login
    profile_picture_url: Optional[str] = None      # URL o path de la foto
    favorites: list[str] = []                   # IDs de eventos favoritos
    attended_events: list[str] = []             # IDs de eventos asistidos
    reviews: list[EventReview] = []               # IDs de eventos revisados
    following: list[str] = []                   # IDs de usuarios que sigue

    class Settings:
        name = "users"


class Event(Document): 
    name: str
    description: Optional[str] = None
    date: datetime
    pictures: list[str] = []      # Cloudinary image URLs
    location: Optional[str] = None
    price: Optional[float] = None
    organizer: User
    attendees: list[str] = []    # IDs de usuarios asistentes
    categories: list[CategoriaBQ] = []   # Categorías culturales del evento (ver CategoriaBQ)

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