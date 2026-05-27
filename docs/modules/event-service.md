# 🔹 Module Reference: Event Service (`event-service`)

The **Event Service** handles the creation, categorization, search, and user attendance registry for events. It runs internally on port `4003`.

---

## 📖 Explanation
The event service controls the catalog of cultural and social events in Barranquilla. It defines what an event is, links events to organizers (User document schemas), filters events by categories (e.g., *champeta*, *gastronomía*), and processes registration/attendance. Event publishing operations require a session JWT whose role is `publisher`; social actions such as attendance and reviews remain available without publisher RBAC.

---

## 📦 Libraries Utilized

*   `beanie` & `motor`: Asynchronous ODM mapping the `events` and `users` collections.
*   `PyJWT`: Decodes session tokens to enforce publisher-only event management.
*   `fastapi`, `uvicorn`, `pydantic-settings`, `python-dotenv`: Web framework and server dependencies.

---

## 🛠️ How It Works

### 1. Document Mapping
The service maps both `User` and `Event` Beanie Documents since `Event` stores the organizer schema directly:

```python
class User(Document):
    name: str
    email: EmailStr
    role: Literal["user", "publisher"] = "user"
    fcm_token: Optional[str] = None
    profile_picture: Optional[str] = None
    favorites: list[str] = []
    attended_events: list[str] = []

    class Settings:
        name = "users"

class Event(Document): 
    name: str
    description: Optional[str] = None
    date: str
    picture: Optional[list[str]] = None
    location: Optional[str] = None
    organizer: User                         # User object embedded/assigned
    attendees: list[str] = []               # Array of user IDs
    categories: list[str] = []              # Categories array

    class Settings:
        name = "events"
```

### 2. Publisher Authorization
The routes that create, update, delete, or manage images for events depend on `require_publisher`. The dependency validates the bearer token with the shared `JWT_SECRET` and rejects non-publisher users with `403`.

Publisher-only endpoints:
*   `POST /events/`
*   `POST /events/{user_id}/events`
*   `PUT /events/{event_id}`
*   `DELETE /events/{event_id}`
*   `POST /events/{event_id}/upload-image`
*   `DELETE /events/{event_id}/images`

### 3. Dual-Collection Synchronization
When a user clicks "Attend Event", the database updates both collections in a single flow:
1. The user's ID is appended to the event's `attendees` array.
2. The event's ID is appended to the user's `attended_events` array.

```python
@router.post("/{event_id}/attend")
async def attend_event(event_id: str, user_id: str):
    event = await Event.get(event_id)
    user = await User.get(user_id)
    
    # 1. Update event attendees
    if user_id not in event.attendees:
        event.attendees.append(user_id)
        await event.save()
    
    # 2. Update user attended_events
    if event_id not in user.attended_events:
        user.attended_events.append(event_id)
        await user.save()
    
    return {"message": "User is now attending the event"}
```

