from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from typing import Literal, Optional, List
from datetime import datetime, date as date_datetime
import enum

from app.models import Transaction


class LoginInApp(BaseModel):
    email: EmailStr
    password: str


class CheckEmail(BaseModel):
    email: EmailStr


# --- USER ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    language: Optional[str] = "en"
    currency: Optional[str] = "USD"
    is_subscribed: Optional[bool] = False
    subscription_id: Optional[str] = None
    subscription_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    language: Optional[str] = None
    currency: Optional[str] = None


class UserInDBBase(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserOut(UserInDBBase):
    pass


class RegistrationInput(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    language: Optional[str] = "en"
    currency: Optional[str] = "USD"


# --- TRANSACTION ---


class TransactionBase(BaseModel):
    type: Literal["income", "expense"]
    amount: float
    currency: str
    category: Optional[str] = None
    tx_date: datetime


class TransactionCreate(TransactionBase):
    pass


class TransactionInDBBase(TransactionBase):
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class TransactionOut(TransactionInDBBase):
    pass


class AnalyticsTransaction(BaseModel):
    id: int
    tx_date: date_datetime = Field(alias="date")
    amount: float
    currency: str
    category: Optional[str] = None
    type: Literal["income", "expense"]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # replace datetime to midnight
    @model_validator(mode="before")
    def replace_datetime(cls, values: Transaction):
        if values.tx_date:
            values.tx_date = values.tx_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        return values


class AnalyticsGroupedTransaction(BaseModel):
    # date is aliased to tx_date
    tx_date: date_datetime = Field(alias="date")
    amount: float

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AnalyticsTransactionOut(BaseModel):
    last_income_transactions: List[AnalyticsTransaction]
    last_expense_transactions: List[AnalyticsTransaction]
    all_income_transactions: List[AnalyticsGroupedTransaction]
    all_expense_transactions: List[AnalyticsGroupedTransaction]
    income_today_amount: float
    expense_today_amount: float
    income_month_amount: float
    expense_month_amount: float
