from fastapi import APIRouter, HTTPException
from .firebase import send_push
from .models import DirectPushRequest, DispatchRequest, GenericResponse
from .notifier import dispatch_notifications

router = APIRouter(
    tags=["notifications"]
)


@router.post("/send-direct", response_model=GenericResponse, summary="Send direct push to a token")
async def send_direct_push(request: DirectPushRequest):
    """Send a single push notification to a specific FCM token."""
    try:
        await send_push(
            token=request.token,
            title=request.title,
            body=request.body,
            data=request.data,
        )
        return GenericResponse(status="success", message="Notification dispatched")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dispatch", response_model=GenericResponse, summary="Dispatch push and email to multiple users")
async def dispatch(request: DispatchRequest):
    """Dispatch notifications (push + email) in parallel to a list of users.

    The `usuarios` list accepts objects with `id`, optional `email` and optional `fcm_token`.
    """
    try:
        await dispatch_notifications(
            usuarios=[u.dict() for u in request.usuarios],
            title=request.title,
            body=request.body,
            data=request.data,
        )
        return GenericResponse(status="success", message="Dispatch completed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    