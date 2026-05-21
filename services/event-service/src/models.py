from typing import Optional
from beanie import Document
from pydantic import BaseModel, EmailStr, field_validator, conint
from .categories import CategoriaBQ
from datetime import datetime


class EventReview(BaseModel):
    event_id: str
    review_text: str  # renaming to review_text avoids confusion with the parent list name
    star: conint(ge=1, le=5)

class UserReview(BaseModel):
    user_id: str
    review_text: str
    star: conint(ge=1, le=5)

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
    organizer: str
    attendees: list[str] = []    # IDs de usuarios asistentes
    categories: list[CategoriaBQ] = []   # Categorías culturales del evento (ver CategoriaBQ)
    reviews: list[UserReview] = []       # Reseñas del evento hechas por usuarios

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%d/%m/%Y %H:%M")
            except ValueError:
                raise ValueError("Formato de fecha inválido. Usa dd/mm/yyyy hh:mm")
        return v

    @field_validator("categories", mode="before")
    @classmethod
    def normalize_categories(cls, v):
        """
        Acepta varias formas de entrada para `categories`:
        - lista de subcategorías: ["champeta", "cumbia"]
        - lista de dicts padre->sublistas: [{"música": ["champeta"]}]
        Normaliza a una lista de `CategoriaBQ`.
        """
        if v is None:
            return []

        vals: list = []
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    for _k, sublist in item.items():
                        if isinstance(sublist, list):
                            vals.extend(sublist)
                        else:
                            vals.append(sublist)
                else:
                    vals.append(item)
        else:
            # Si no es lista, devolvemos como está (pydantic lanzará el error)
            return v

        normalized: list[CategoriaBQ] = []
        for s in vals:
            if isinstance(s, CategoriaBQ):
                normalized.append(s)
                continue
            try:
                normalized.append(CategoriaBQ(s))
            except Exception:
                # intentamos limpiar strings ocasionales
                found = None
                for member in CategoriaBQ:
                    if member.value == s:
                        found = member
                        break
                if found:
                    normalized.append(found)
                else:
                    raise ValueError(f"Categoría inválida: {s}")

        return normalized

    class Settings:
        name = "events"