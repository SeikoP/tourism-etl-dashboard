from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Place(BaseModel):
    id: int
    name: str
    city: str
    country: str

@router.get("/places/sample")
async def sample_places():
    return [
        {"id": 1, "name": "Đền Ngọc Sơn", "city": "Hà Nội", "country": "Vietnam"}
    ]

@router.post("/booking")
async def create_booking(payload: dict):
    # mock booking endpoint
    return {"booking_id": "BK-1234", "status": "confirmed", "payload": payload}
