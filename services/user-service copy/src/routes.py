from fastapi import APIRouter, HTTPException
from .models import User

router = APIRouter()


@router.get("/")
async def list_users():
    return await User.find_all().to_list()


@router.get("/{user_id}")
async def get_user(user_id: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", status_code=201)
async def create_user(user: User):
    return await user.insert()
