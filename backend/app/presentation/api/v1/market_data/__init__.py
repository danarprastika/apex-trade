""""""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_market_data() -> dict[str, str]:
    return {"message": "market_data endpoint"}
