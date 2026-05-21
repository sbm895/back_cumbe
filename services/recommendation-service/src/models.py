from beanie import Document
from pydantic import EmailStr, field_validator
from typing import Optional
from .categories import CategoriaBQ
from datetime import datetime


class User(Document):
    name: str
    email: EmailStr
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
    organizer: User
    attendees: list[str] = []
    categories: list[CategoriaBQ] = []

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