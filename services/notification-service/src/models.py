from pydantic import BaseModel

class DirectPushRequest(BaseModel):
    token: str
    title: str
    body: str
    data: dict = {}