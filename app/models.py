from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    ARRAY,
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Float,
    Enum,
    Boolean,
    Text,
    func,
    Numeric,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(default="expense")  # 'income' or 'expense'
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    tx_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped["User"] = relationship("User", back_populates="transactions")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )
    telegram_chat_id: Mapped[str] = mapped_column(String(100), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(5), default="en")
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_registered_from_telegram: Mapped[bool] = mapped_column(Boolean, default=False)

    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_id: Mapped[str] = mapped_column(String(100), nullable=True)
    subscription_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    subscription_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    liqpay_order_id: Mapped[str] = mapped_column(String(100), nullable=True)
    order_id: Mapped[str] = mapped_column(String(100), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)

    transactions: Mapped[List[Transaction]] = relationship(
        "Transaction", back_populates="user"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
