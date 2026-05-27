from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from .auth import require_publisher
from .models import User, Event, UserReview
from .categories import CategoriaBQ
import cloudinary.uploader

router = APIRouter()


@router.get("/categories", response_model=dict[str, list[str]])
async def get_categories():
    """Retorna todas las categorías culturales agrupadas por su categoría padre."""
    from .categories import PADRE_A_SUBCATEGORIAS
    return {
        padre.value: [sub.value for sub in subs] 
        for padre, subs in PADRE_A_SUBCATEGORIAS.items()
    }


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
    
@router.get("/incoming")
async def get_incoming_events():
    now = datetime.now(timezone.utc)
    next_24h = now + timedelta(hours=24)
    
    events = await Event.find({
        "date": {"$gte": now, "$lte": next_24h}
    }).to_list()
    return events



@router.get("/category/{category_name}")
async def get_events_by_category(category_name: str):
    """Busca eventos. category_name puede ser una categoría padre (ej. 'música') o una subcategoría (ej. 'champeta')."""
    from .categories import CategoriaPadre, PADRE_A_SUBCATEGORIAS
    
    try:
        # Si es una categoría padre, buscamos todas las subcategorías que le pertenecen
        padre = CategoriaPadre(category_name)
        subs = PADRE_A_SUBCATEGORIAS[padre]
        events = await Event.find({"categories": {"$in": subs}}).to_list()
        return events
    except ValueError:
        # Si falla, asumimos que es una subcategoría directa (ej. 'champeta')
        events = await Event.find({"categories": category_name}).to_list()
        return events


@router.get("/{event_id}")
async def get_event(event_id: str):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}")
async def update_event(
    event_id: str,
    event_data: Event,
    _publisher: dict[str, str] = Depends(require_publisher),
):
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
async def delete_event(
    event_id: str,
    _publisher: dict[str, str] = Depends(require_publisher),
):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    await event.delete()
    return {"message": "Event deleted successfully"}

@router.post("/", status_code=201)
async def create_event(
    event: Event,
    _publisher: dict[str, str] = Depends(require_publisher),
):
    # `event.organizer` ahora guarda solo el id (str)
    if event.organizer and event.organizer not in event.attendees:
        event.attendees.append(event.organizer)

    # Insertar el evento primero para obtener su id
    inserted_event = await event.insert()

    # Intentar actualizar la lista de `attended_events` del usuario organizador
    try:
        if inserted_event.organizer:
            user = await User.get(inserted_event.organizer)
            if user and str(inserted_event.id) not in user.attended_events:
                user.attended_events.append(str(inserted_event.id))
                await user.save()
    except Exception:
        # No bloquear la creación del evento si falla la actualización del usuario
        pass

    return inserted_event

@router.post("/{user_id}/events")
async def create_event_for_user(
    user_id: str,
    event: Event,
    _publisher: dict[str, str] = Depends(require_publisher),
):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Guardamos solo el id del organizador
    event.organizer = user_id
    if user_id not in event.attendees:
        event.attendees.append(user_id)

    # Insertar y luego actualizar el documento del usuario
    inserted_event = await event.insert()
    if str(inserted_event.id) not in user.attended_events:
        user.attended_events.append(str(inserted_event.id))
        await user.save()

    return inserted_event

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





@router.post("/{event_id}/reviews", status_code=201)
async def add_review_to_event(event_id: str, review: UserReview):
    """Recibe una reseña de un usuario y la guarda en el modelo del evento."""
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.reviews.append(review)
    await event.save()
    return review

@router.patch("/{event_id}/reviews/{user_id}", status_code=200, response_model=UserReview)
async def update_review(event_id: str, user_id: str, review: UserReview):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for i, r in enumerate(event.reviews):
        if r.user_id == user_id:
            event.reviews[i] = review
            await event.save()
            return review

    raise HTTPException(status_code=404, detail="Review not found")


@router.delete("/{event_id}/reviews/{user_id}", status_code=204)
async def delete_review(event_id: str, user_id: str):
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    original_len = len(event.reviews)
    event.reviews = [r for r in event.reviews if r.user_id != user_id]

    if len(event.reviews) == original_len:
        raise HTTPException(status_code=404, detail="Review not found")

    await event.save()

@router.get("/{event_id}/reviews")
async def get_event_reviews(event_id: str):
    """Retorna la lista de todas las reseñas que los usuarios han dejado para este evento."""
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event.reviews




@router.post(
    "/{event_id}/upload-image",
    response_model=EventImageUploadResponse,
    status_code=200,
    summary="Upload Event Image",
    tags=["Images"],
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
async def upload_event_image(
    event_id: str,
    file: UploadFile = File(...),
    _publisher: dict[str, str] = Depends(require_publisher),
):
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
    
@router.delete(
    "/{event_id}/images",
    status_code=200,
    summary="Delete Event Image",
    tags=["Images"],
    description="Elimina una imagen específica de la lista de imágenes del evento en la base de datos.",
    responses={
        200: {"description": "Imagen eliminada exitosamente"},
        404: {"description": "Evento no encontrado o imagen no encontrada en la lista"},
    },
)
async def delete_event_image(
    event_id: str,
    image_url: str,
    _publisher: dict[str, str] = Depends(require_publisher),
):
    """
    ## Eliminar imagen de evento

    - **event_id**: ID del evento
    - **image_url**: URL exacta de la imagen a eliminar
    """
    event = await Event.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if image_url not in event.pictures:
        raise HTTPException(status_code=404, detail="Image not found in event")

    event.pictures.remove(image_url)
    await event.save()

    return {"message": "Image deleted", "event_id": event_id, "url": image_url}
    
