from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from .models import User, Event
import cloudinary.uploader

router = APIRouter()


class EventImageUploadResponse(BaseModel):
    """Response model for event image upload."""
    url: str
    event_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://res.cloudinary.com/your_cloud/image/upload/v1234567890/abcdef.jpg",
                "event_id": "507f1f77bcf86cd799439011"
            }
        }


@router.get("/popular")
async def get_popular_events():
    try:
        events = await Event.find().to_list()
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching popular events: {str(e)}")


@router.get("/category/{category_name}")
async def get_events_by_category(category_name: str):
    events = await Event.find({"categories": category_name}).to_list()
    return events


@router.get("/{event_id}")
async def get_event(event_id: str):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}")
async def update_event(event_id: str, event_data: Event):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.name = event_data.name
    event.description = event_data.description
    event.date = event_data.date
    event.pictures = event_data.pictures
    event.location = event_data.location
    event.price = event_data.price
    await event.save()
    
    return event

@router.delete("/{event_id}")
async def delete_event(event_id: str):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    await event.delete()
    return {"message": "Event deleted successfully"}

@router.post("/", status_code=201)
async def create_event(event: Event):
    return await event.insert()

@router.post("/{user_id}/events")
async def create_event_for_user(user_id: str, event: Event):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    event.organizer = user
    return await event.insert()

@router.post("/{event_id}/attend")
async def attend_event(event_id: str, user_id: str):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_id not in event.attendees:
        event.attendees.append(user_id)
        await event.save()
    
    if event_id not in user.attended_events:
        user.attended_events.append(event_id)
        await user.save()
    
    return {"message": "User is now attending the event"}

@router.delete("/{event_id}/attend")
async def leave_event(event_id: str, user_id: str):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id in event.attendees:
        event.attendees.remove(user_id)
        await event.save()

    if event_id in user.attended_events:
        user.attended_events.remove(event_id)
        await user.save()

    return {"message": "User is no longer attending the event"}

@router.get("/{event_id}/attendees")
async def get_event_attendees(event_id: str):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.attendees

@router.get("/popular")
async def get_popular_events(limit: int = 10):
    try:
        events = await Event.find().limit(limit).to_list()
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching popular events: {str(e)}")


@router.post(
    "/{event_id}/upload-image",
    response_model=EventImageUploadResponse,
    status_code=200,
    summary="Upload Event Image",
    tags=["Events", "Images"],
    responses={
        404: {
            "description": "Event not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Event not found"}
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
async def upload_event_image(event_id: str, file: UploadFile = File(...)):
    """
    Upload an image for an event to Cloudinary.
    
    - **event_id**: The ID of the event to upload the image for
    - **file**: The image file to upload (multipart/form-data)
    
    Returns the Cloudinary secure URL and saves it to the Event document in MongoDB.
    """
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    try:
        contents = await file.read()
        result = cloudinary.uploader.upload(contents)
        secure_url = result["secure_url"]
        
        event.pictures.append(secure_url)
        await event.save()
        
        return {"url": secure_url, "event_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")
    