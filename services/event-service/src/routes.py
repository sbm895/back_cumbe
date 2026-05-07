from fastapi import APIRouter, HTTPException
from .models import User, Event

router = APIRouter()


@router.get("/{event_id}")
async def get_event(event_id: str):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

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
