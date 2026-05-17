from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from .models import User
from .auth import hash_password, verify_password, create_access_token, verify_token

router = APIRouter()


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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


@router.get("/verify-token/{token}")
async def verify_token_endpoint(token: str):
    """Verify a JWT token and return the user ID if valid."""
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {"user_id": user_id}



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

