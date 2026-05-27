from beanie import Document
from pydantic import EmailStr, field_validator
from typing import Literal, Optional
from .categories import CategoriaBQ
from datetime import datetime


class User(Document):
    name: str
    email: EmailStr
    role: Literal["user", "publisher"] = "user"
    fcm_token: Optional[str] = None
    profile_picture_url: Optional[str] = None
    favorites: list[str] = []
    attended_events: list[str] = []
    following: list[str] = []

    class Settings:
        name = "users"


class Event(Document):
    name: str
    description: Optional[str] = None
    date: datetime
    pictures: list[str] = []
    location: Optional[str] = None
    price: Optional[float] = None
    organizer: str
    attendees: list[str] = []
    categories: list[CategoriaBQ] = []

 
    class Settings:
        name = "events"
