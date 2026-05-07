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

@router.put("/{user_id}")
async def update_user(user_id: str, user_data: User):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.name = user_data.name
    user.email = user_data.email
    user.fcm_token = user_data.fcm_token
    user.profile_picture = user_data.profile_picture
    await user.save()
    
    return user

@router.put("/{user_id}/fcm_token")
async def update_fcm_token(user_id: str, fcm_token: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.fcm_token = fcm_token
    await user.save()

    return {"message": "FCM token updated successfully"}

@router.get("/{user_id}/fcm_token")
async def get_fcm_token(user_id: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"fcm_token": user.fcm_token}

@router.delete("/{user_id}")
async def delete_user(user_id: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await user.delete()
    return {"message": "User deleted successfully"} 

