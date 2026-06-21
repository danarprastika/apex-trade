""""""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_portfolio() -> dict[str, str]:
    return {"message": "portfolio endpoint"}
