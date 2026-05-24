from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Header
from pydantic import BaseModel, EmailStr, conint
from .models import User, EventReview
from .auth import hash_password, verify_password, create_access_token, verify_token
import cloudinary.uploader

router = APIRouter()


class UserImageUploadResponse(BaseModel):
    """Response model for user profile picture upload."""
    url: str
    user_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://res.cloudinary.com/your_cloud/image/upload/v1234567890/abcdef.jpg",
                "user_id": "507f1f77bcf86cd799439011"
            }
        }


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CreateReviewRequest(BaseModel):
    event_id: str
    review_text: str
    star: conint(ge=1, le=5)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class BatchUserRequest(BaseModel):
    ids: list[str]

@router.post("/batch", response_model=list[User])
async def get_users_batch(request: BatchUserRequest):
    from beanie import PydanticObjectId
    object_ids = [PydanticObjectId(uid) for uid in request.ids if PydanticObjectId.is_valid(uid)]
    users = await User.find({"_id": {"$in": object_ids}}).to_list()
    return users


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(request: SignupRequest):
    """Create a new user with email and password, return JWT token."""
    existing_user = await User.find_one(User.email == request.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = hash_password(request.password)
    user = User(
        name=request.name,
        email=request.email,
        hashed_password=hashed_pwd,
    )
    await user.insert()
    
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user with email and password, return JWT token."""
    user = await User.find_one(User.email == request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


def get_bearer_token(authorization: str | None = Header(None)) -> str | None:
    if authorization is None:
        return None
    if not authorization.startswith("Bearer "):
        return None
    return authorization.split("Bearer ", 1)[1].strip()


@router.get("/verify-token/{token}")
async def verify_token_endpoint(token: str):
    """Verify a JWT token and return the user ID if valid."""
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {"user_id": user_id}


@router.post("/logout")
async def logout(authorization: str = Depends(get_bearer_token)):
    """Log the user out by verifying the bearer token and returning a success message."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    user_id = verify_token(authorization)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"message": "Logged out successfully"}


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
    user.profile_picture_url = user_data.profile_picture_url
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


@router.post("/{user_id}/reviews", status_code=201, response_model=CreateReviewRequest)
async def add_review(user_id: str, review: CreateReviewRequest):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.reviews.append(review)
    await user.save()

    return review

@router.put("/{user_id}/reviews/{event_id}", status_code=200, response_model=EventReview)
async def update_review(user_id: str, event_id: str, review: EventReview):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for i, r in enumerate(user.reviews):
        if r.event_id == event_id:
            user.reviews[i] = review
            await user.save()
            return review

    raise HTTPException(status_code=404, detail="Review not found")


@router.delete("/{user_id}/reviews/{event_id}", status_code=204)
async def delete_review(user_id: str, event_id: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    original_len = len(user.reviews)
    user.reviews = [r for r in user.reviews if r.event_id != event_id]

    if len(user.reviews) == original_len:
        raise HTTPException(status_code=404, detail="Review not found")

    await user.save()



@router.delete("/{user_id}")
async def delete_user(user_id: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await user.delete()
    return {"message": "User deleted successfully"}


@router.post(
    "/{user_id}/upload-profile-picture",
    response_model=UserImageUploadResponse,
    status_code=200,
    summary="Upload User Profile Picture",
    tags=["Users", "Images"],
    responses={
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            },
        },
        500: {
            "description": "Error uploading image to Cloudinary",
            "content": {
                "application/json": {
                    "example": {"detail": "Error uploading image: Cloudinary API error"}
                }
            },
        },
    },
)
async def upload_profile_picture(user_id: str, file: UploadFile = File(...)):
    """
    Upload a profile picture for a user to Cloudinary.
    
    - **user_id**: The ID of the user to upload the profile picture for
    - **file**: The image file to upload (multipart/form-data)
    
    Returns the Cloudinary secure URL and saves it to the User document in MongoDB.
    """
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        contents = await file.read()
        result = cloudinary.uploader.upload(contents)
        secure_url = result["secure_url"]
        
        user.profile_picture_url = secure_url
        await user.save()
        
        return {"url": secure_url, "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")


@router.post(
    "/{user_id}/favorites/{event_id}",
    summary="Add Event to Favorites",
    description="Añade un evento a la lista de favoritos del usuario.",
    tags=["Interactions"],
    responses={
        200: {"description": "Event added to favorites successfully"},
        404: {"description": "User not found"}
    }
)
async def add_favorite(user_id: str, event_id: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if event_id not in user.favorites:
        user.favorites.append(event_id)
        await user.save()
    return {"message": "Event added to favorites"}

@router.delete(
    "/{user_id}/favorites/{event_id}",
    summary="Remove Event from Favorites",
    description="Elimina un evento de la lista de favoritos del usuario.",
    tags=["Interactions"],
    responses={
        200: {"description": "Event removed from favorites successfully"},
        404: {"description": "User not found"}
    }
)
async def remove_favorite(user_id: str, event_id: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if event_id in user.favorites:
        user.favorites.remove(event_id)
        await user.save()
    return {"message": "Event removed from favorites"}

@router.post(
    "/{user_id}/follow/{target_user_id}",
    summary="Follow a User",
    description="Permite que un usuario siga a otro. Importante para el sistema de recomendación por adyacencia (filtrado colaborativo).",
    tags=["Interactions"],
    responses={
        200: {"description": "Successfully followed user"},
        400: {"description": "User cannot follow themselves"},
        404: {"description": "User or target user not found"}
    }
)
async def follow_user(user_id: str, target_user_id: str):
    if user_id == target_user_id:
        raise HTTPException(status_code=400, detail="User cannot follow themselves")
    
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    target = await User.get(target_user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")
        
    if target_user_id not in user.following:
        user.following.append(target_user_id)
        await user.save()
        
    return {"message": f"Successfully followed user {target_user_id}"}


@router.delete(
    "/{user_id}/follow/{target_user_id}",
    summary="Unfollow a User",
    description="Permite que un usuario deje de seguir a otro.",
    tags=["Interactions"],
    responses={
        200: {"description": "Successfully unfollowed user"},
        404: {"description": "User or target user not found"}
    }
)
async def unfollow_user(user_id: str, target_user_id: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    target = await User.get(target_user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")
        
    if target_user_id in user.following:
        user.following.remove(target_user_id)
        await user.save()
        
    return {"message": f"Successfully unfollowed user {target_user_id}"}

