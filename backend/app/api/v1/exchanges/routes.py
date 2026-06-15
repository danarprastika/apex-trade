from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_exchange_service
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.exchange import ExchangeAccountCreate, ExchangeAccountRead, ExchangeCreate, ExchangeRead
from app.services.exchange_service import ExchangeService

router = APIRouter()


@router.get("/", response_model=list[ExchangeRead])
def list_exchanges(
    exchange_service: ExchangeService = Depends(get_exchange_service),
):
    return exchange_service.list_exchanges()


@router.post("/", response_model=ExchangeRead, status_code=201)
def create_exchange(
    payload: ExchangeCreate,
    current_user: User = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service),
):
    if current_user.role not in {ROLE_SUPER_ADMIN, ROLE_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return exchange_service.create_exchange(payload.name, payload.exchange_type, payload.status)


@router.post("/accounts", response_model=ExchangeAccountRead, status_code=201)
def create_exchange_account(
    payload: ExchangeAccountCreate,
    current_user: User = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service),
):
    return exchange_service.create_account(
        user_id=current_user.id,
        exchange_id=payload.exchange_id,
        api_key=payload.api_key.get_secret_value(),
        api_secret=payload.api_secret.get_secret_value(),
        is_testnet=payload.is_testnet,
    )


@router.get("/accounts", response_model=list[ExchangeAccountRead])
def list_accounts(
    current_user: User = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service),
):
    return exchange_service.list_accounts(current_user.id)


@router.post("/accounts/{account_id}/test", response_model=dict)
def test_connection(
    account_id: str,
    current_user: User = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service),
):
    return exchange_service.test_connection(account_id, current_user.id)


@router.post("/accounts/{account_id}/sync", response_model=dict)
def sync_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service),
):
    return exchange_service.sync_account(account_id, current_user.id)



