from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update, delete, cast, Date
from typing import List, Optional

from app.models import User, Transaction


# ---------- USER ----------
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user_id: int, data: dict) -> Optional[User]:
    await db.execute(update(User).where(User.id == user_id).values(**data))
    await db.commit()
    return await get_user(db, user_id)


# --------- TRANSACTION ----------
async def create_transaction(db: AsyncSession, transaction: Transaction) -> Transaction:
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


async def get_transaction(
    db: AsyncSession, tx_id: int, user_id: int
) -> Optional[Transaction]:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == tx_id, Transaction.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def delete_transaction(db: AsyncSession, tx_id: int, user_id: int) -> None:
    await db.execute(
        delete(Transaction).where(
            Transaction.id == tx_id, Transaction.user_id == user_id
        )
    )
    await db.commit()


async def get_transactions(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: date = None,
    end_date: date = None,
    order: str = "desc",
) -> List[Transaction]:
    query = select(Transaction).where(Transaction.user_id == user_id)
    if start_date:
        query = query.where(Transaction.tx_date >= start_date)
    if end_date:
        query = query.where(Transaction.tx_date <= end_date)
    query = query.order_by(
        Transaction.tx_date.desc() if order == "desc" else Transaction.tx_date.asc()
    )
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_transactions_by_type(
    db: AsyncSession,
    user_id: int,
    tx_type: str,
    limit: int = None,
    start_date: date = None,
    end_date: date = None,
) -> List[Transaction]:
    query = select(Transaction).where(
        Transaction.user_id == user_id, Transaction.type == tx_type
    )
    if start_date:
        query = query.where(Transaction.tx_date >= start_date)
    if end_date:
        query = query.where(Transaction.tx_date <= end_date)
    query = query.order_by(Transaction.tx_date.desc())
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_transactions_by_type_grouped(
    db: AsyncSession,
    user_id: int,
    tx_type: str,
    start_date: date = None,
    end_date: date = None,
) -> List[Transaction]:
    query = select(
        cast(Transaction.tx_date, Date).label("tx_date"),
        func.sum(Transaction.amount).label("amount"),
    ).where(Transaction.user_id == user_id, Transaction.type == tx_type)
    query = query.group_by(cast(Transaction.tx_date, Date))
    query = query.order_by(cast(Transaction.tx_date, Date).asc())
    result = await db.execute(query)
    return result.all()


async def get_transactions_amount(
    db: AsyncSession,
    user_id: int,
    tx_type: str,
    start_date: date = None,
    end_date: date = None,
) -> float:
    query = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.type == tx_type
    )
    if start_date:
        query = query.where(Transaction.tx_date >= start_date)
    if end_date:
        query = query.where(Transaction.tx_date <= end_date)
    result = await db.execute(query)
    return result.scalar() or 0.0
