from fastapi import APIRouter, HTTPException
from collections import Counter
from beanie import PydanticObjectId
import httpx
import os

from .models import User, Event

router = APIRouter()

EVENT_SERVICE_URL = os.getenv("EVENT_SERVICE_URL", "https://back-cumbe-events.achesito.xyz")


async def _popular_events(limit: int = 10):
    """Fetch popular events from event-service endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EVENT_SERVICE_URL}/events/popular",
                params={"limit": limit},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching popular events: {str(e)}")


@router.get("/{user_id}")
async def get_recommendations(user_id: str, limit: int = 10):
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    seen_ids = set(user.favorites + user.attended_events)

    if not seen_ids:
        return await _popular_events(limit)

    seen_events = await Event.find(
        {"_id": {"$in": [PydanticObjectId(i) for i in seen_ids]}}
    ).to_list()

    category_counts = Counter()
    for event in seen_events:
        for cat in event.categories:
            category_counts[cat] += 1

    if not category_counts:
        return await _popular_events(limit)

    candidates = await Event.find({
        "_id": {"$nin": [PydanticObjectId(i) for i in seen_ids]},
        "categories": {"$in": list(category_counts.keys())}
    }).to_list()

    def score(event: Event) -> int:
        return sum(category_counts[c] for c in event.categories if c in category_counts)

    ranked = sorted(candidates, key=score, reverse=True)[:limit]
    return ranked