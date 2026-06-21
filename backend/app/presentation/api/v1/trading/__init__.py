""""""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_trades() -> dict[str, str]:
    return {"message": "trading endpoint"}
