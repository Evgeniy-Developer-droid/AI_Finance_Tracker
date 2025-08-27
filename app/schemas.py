from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from typing import Literal, Optional, List
from datetime import datetime, date
import enum


# --- USER ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    language: Optional[str] = "en"
    currency: Optional[str] = "USD"


class UserCreate(UserBase):
    password: str


class UserInDBBase(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


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
