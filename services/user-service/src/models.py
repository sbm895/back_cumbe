from typing import Optional
from beanie import Document
from pydantic import BaseModel, EmailStr, conint


class EventReview(BaseModel):
    event_id: str
    review_text: str  # renaming to review_text avoids confusion with the parent list name
    star: conint(ge=1, le=5)


class User(Document):
    name: str
    email: EmailStr
    hashed_password: Optional[str] = None
    fcm_token: Optional[str] = None  # se actualiza cada login
    profile_picture_url: Optional[str] = None                # Cloudinary image URL
    favorites: list[str] = []                   # IDs de eventos favoritos
    attended_events: list[str] = []             # IDs de eventos asistidos
    reviews: list[EventReview] = []               # IDs de eventos revisados



    class Settings:
        name = "users"