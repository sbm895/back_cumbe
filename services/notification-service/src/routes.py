from fastapi import APIRouter, HTTPException
from firebase import send_push
from models import DirectPushRequest

router = APIRouter()


@router.post("/send-direct")
async def send_direct_push(request: DirectPushRequest):
    try:
        await send_push(
            token=request.token,
            title=request.title,
            body=request.body,
            data=request.data
        )
        return {"status": "success", "message": "Notification dispatched"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    