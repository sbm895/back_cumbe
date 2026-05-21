from beanie import Document
from pydantic import EmailStr
from typing import Optional
from .categories import CategoriaBQ


class User(Document):
    name: str
    email: EmailStr
    fcm_token: Optional[str] = None
    profile_picture_url: Optional[str] = None
    favorites: list[str] = []
    attended_events: list[str] = []

    class Settings:
        name = "users"


class Event(Document):
    name: str
    description: Optional[str] = None
    date: str
    pictures: list[str] = []
    location: Optional[str] = None
    price: Optional[float] = None
    organizer: User
    attendees: list[str] = []
    categories: list[CategoriaBQ] = []

    class Settings:
        name = "events"