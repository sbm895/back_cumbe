from typing import Optional
from beanie import Document
from pydantic import BaseModel, EmailStr
from .categories import CategoriaBQ


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

    class Settings:
        name = "users"


class Event(Document): 
    name: str
    description: Optional[str] = None
    date: str
    pictures: list[str] = []      # Cloudinary image URLs
    location: Optional[str] = None
    price: Optional[float] = None
    organizer: User
    attendees: list[str] = []    # IDs de usuarios asistentes
    categories: list[CategoriaBQ] = []   # Categorías culturales del evento (ver CategoriaBQ)

    class Settings:
        name = "events"