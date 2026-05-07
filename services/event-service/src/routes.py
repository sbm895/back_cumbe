from fastapi import APIRouter, HTTPException
from .models import User, Event

router = APIRouter()


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
    event.picture = event_data.picture
    event.location = event_data.location
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
async def get_popular_events():
    # This is a simplified version - you might want to implement actual popularity logic
    events = await Event.find().to_list()
    return events

@router.get("/category/{category_name}")
async def get_events_by_category(category_name: str):
    events = await Event.find({"categories": category_name}).to_list()
    return events
    