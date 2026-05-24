from pydantic import BaseModel, EmailStr
from typing import Any, Dict, List


class DirectPushRequest(BaseModel):
    token: str
    title: str
    body: str
    data: Dict[str, Any] = {}


class UserContact(BaseModel):
    id: str
    email: EmailStr | None = None
    fcm_token: str | None = None


class DispatchRequest(BaseModel):
    usuarios: List[UserContact]
    title: str
    body: str
    data: Dict[str, Any] = {}


class GenericResponse(BaseModel):
    status: str
    message: str | None = None