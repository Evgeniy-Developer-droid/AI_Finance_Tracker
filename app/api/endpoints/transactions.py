from datetime import datetime, timedelta, date
from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import (
    AnalyticsTransactionOut,
    TransactionCreate,
    TransactionOut,
    AnalyticsGroupedTransaction,
    AnalyticsTransaction,
)
from app.models import User, Transaction
from app.crud import (
    create_transaction,
    get_transactions_amount,
    get_transactions_by_type,
    get_transaction,
    delete_transaction,
    get_transactions,
    get_transactions_by_type_grouped,
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
    order: str = "desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TransactionOut]:
    start = start or datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    end = end or datetime.now()
    return await get_transactions(
        db,
        current_user.id,
        start_date=start,
        end_date=end,
        skip=page * limit,
        limit=limit,
        order=order,
    )


@router.get("/dashboard/analytics", response_model=AnalyticsTransactionOut)
async def get_transactions_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsTransactionOut:
    start_date = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0, day=1
    )
    end_date = datetime.now()
    income_last_transactions = await get_transactions_by_type(
        db,
        user_id=current_user.id,
        tx_type="income",
        start_date=start_date,
        end_date=end_date,
        limit=5,
    )
    expense_last_transactions = await get_transactions_by_type(
        db,
        user_id=current_user.id,
        tx_type="expense",
        start_date=start_date,
        end_date=end_date,
        limit=5,
    )
    all_income_transactions = await get_transactions_by_type_grouped(
        db=db,
        user_id=current_user.id,
        tx_type="income",
    )
    all_expense_transactions = await get_transactions_by_type_grouped(
        db=db,
        user_id=current_user.id,
        tx_type="expense",
    )
    income_today_amount = await get_transactions_amount(
        db=db,
        user_id=current_user.id,
        tx_type="income",
        start_date=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
        end_date=end_date,
    )
    expense_today_amount = await get_transactions_amount(
        db=db,
        user_id=current_user.id,
        tx_type="expense",
        start_date=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
        end_date=end_date,
    )
    income_month_amount = await get_transactions_amount(
        db=db,
        user_id=current_user.id,
        tx_type="income",
        start_date=start_date,
        end_date=end_date,
    )
    expense_month_amount = await get_transactions_amount(
        db=db,
        user_id=current_user.id,
        tx_type="expense",
        start_date=start_date,
        end_date=end_date,
    )
    return {
        "last_income_transactions": [
            AnalyticsTransaction.model_validate(tx, by_alias=True)
            for tx in income_last_transactions
        ],
        "last_expense_transactions": [
            AnalyticsTransaction.model_validate(tx, by_alias=True)
            for tx in expense_last_transactions
        ],
        "all_income_transactions": [
            AnalyticsGroupedTransaction.model_validate(tx, by_alias=True)
            for tx in all_income_transactions
        ],
        "all_expense_transactions": [
            AnalyticsGroupedTransaction.model_validate(tx, by_alias=True)
            for tx in all_expense_transactions
        ],
        "income_today_amount": income_today_amount,
        "expense_today_amount": expense_today_amount,
        "income_month_amount": income_month_amount,
        "expense_month_amount": expense_month_amount,
    }


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction_endpoint(
    tx_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await delete_transaction(db, tx_id, current_user.id)
