from datetime import timedelta, date
from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import TransactionCreate, TransactionOut
from app.models import User, Transaction
from app.crud import (
    create_transaction,
    get_transaction,
    delete_transaction,
    get_transactions,
)
from app.api.deps import get_current_user

router = APIRouter()


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction_endpoint(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionOut:
    obj = Transaction(user_id=current_user.id, **transaction.model_dump())
    return await create_transaction(db, obj)


@router.get("/{tx_id}", response_model=TransactionOut)
async def get_transaction_endpoint(
    tx_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionOut:
    obj = await get_transaction(db, tx_id, current_user.id)
    if not obj:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return obj


@router.get("", response_model=List[TransactionOut])
async def get_transactions_endpoint(
    start: date = None,
    end: date = None,
    page: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TransactionOut]:
    return await get_transactions(
        db,
        current_user.id,
        start_date=start,
        end_date=end,
        skip=page * limit,
        limit=limit,
    )


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction_endpoint(
    tx_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await delete_transaction(db, tx_id, current_user.id)
