from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.models import Transaction, User
from app.schemas import UserCreate
from app.core.security import get_password_hash
from app.core.config import Settings

settings = Settings()

router = Router()

CURRENCY_MARKUP = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=c)] for c in settings.CURRENCY_CHOICES],
    resize_keyboard=True,
)

MAIN_MARKUP = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Add income"), KeyboardButton(text="Add expense")],
        [KeyboardButton(text="Report"), KeyboardButton(text="Last transactions")],
    ],
    resize_keyboard=True,
)


class Registration(StatesGroup):
    waiting_for_email = State()
    waiting_for_currency = State()


@router.message(F.text == "/start")
async def start_handler(message: types.Message, state: FSMContext):
    async with async_session() as db:
        user = await db.execute(
            select(User).where(User.telegram_chat_id == str(message.chat.id))
        )
        existing_user = user.scalar_one_or_none()

        if existing_user:
            await message.answer(
                "👋 Hi! You are already registered. You can start adding transactions.",
                reply_markup=MAIN_MARKUP,
            )
        else:
            await message.answer(
                "🔐 You are not registered yet. Let's fix that. First, please send your email address."
            )
            await state.set_state(Registration.waiting_for_email)


@router.message(Registration.waiting_for_email, F.text)
async def register_email(message: types.Message, state: FSMContext):
    if "@" not in message.text:
        await message.answer(
            "🚫 Invalid email format. Please send a valid email address."
        )
        return
    async with async_session() as db:
        email_exists = await db.execute(select(User).where(User.email == message.text))
        if email_exists.scalar_one_or_none():
            await message.answer(
                "🚫 This email is already registered. Please use a different email."
            )
            return
        await state.update_data(email=message.text)
        await message.answer(
            "💱 Please choose your default currency:", reply_markup=CURRENCY_MARKUP
        )
        await state.set_state(Registration.waiting_for_currency)


@router.message(
    Registration.waiting_for_currency, F.text.in_(settings.CURRENCY_CHOICES)
)
async def register_currency(message: types.Message, state: FSMContext):
    async with async_session() as db:
        user_data = await state.get_data()
        user = User(
            email=user_data["email"],
            telegram_chat_id=str(message.chat.id),
            is_registered_from_telegram=True,
        )
        db.add(user)
        await db.commit()
        await message.answer(
            "🎉 Great! You are registered now. You can start adding income or expenses.",
            reply_markup=MAIN_MARKUP,
        )
        await state.clear()


class TxInput(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_date = State()


CATEGORY_MARKUP_EXPENSE = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=c)] for c in settings.CATEGORY_CHOICES_EXPENSE],
    resize_keyboard=True,
)

CATEGORY_MARKUP_INCOME = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=c)] for c in settings.CATEGORY_CHOICES_INCOME],
    resize_keyboard=True,
)

DATE_MARKUP = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Today")],
    ],
    resize_keyboard=True,
)


@router.message(F.text.lower() == "add expense")
async def start_expense(message: types.Message, state: FSMContext):
    await state.update_data(type="expense")
    await message.answer(
        "📂 Please choose a category:", reply_markup=CATEGORY_MARKUP_EXPENSE
    )
    await state.set_state(TxInput.waiting_for_category)


@router.message(F.text.lower() == "add income")
async def start_income(message: types.Message, state: FSMContext):
    await state.update_data(type="income")
    await message.answer(
        "📂 Please choose a category:", reply_markup=CATEGORY_MARKUP_INCOME
    )
    await state.set_state(TxInput.waiting_for_category)


@router.message(TxInput.waiting_for_amount, F.text)
async def input_amount(message: types.Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a numeric value.")
        return
    type_data = await state.get_data()
    await state.update_data(amount=message.text)
    await message.answer(
        "📅 Please specify the date with the format YYYY-MM-DD or click 'Today'",
        reply_markup=DATE_MARKUP,
    )
    await state.set_state(TxInput.waiting_for_date)


@router.message(TxInput.waiting_for_category, F.text)
async def input_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("💰 Please specify the amount:")
    await state.set_state(TxInput.waiting_for_amount)


@router.message(TxInput.waiting_for_date, F.text)
async def input_date(message: types.Message, state: FSMContext):
    async with async_session() as db:
        data = await state.get_data()
        user = await db.execute(
            select(User).where(User.telegram_chat_id == str(message.chat.id))
        )
        user_obj = user.scalar_one()

        if message.text.lower() in ["today"]:
            tx_date = datetime.now()
        else:
            try:
                tx_date = datetime.strptime(message.text, "%Y-%m-%d")
            except ValueError:
                await message.answer("❌ Invalid date format. Use YYYY-MM-DD")
                return

        tx = Transaction(
            user_id=user_obj.id,
            type=data["type"],
            amount=float(data["amount"]),
            category=data["category"],
            tx_date=tx_date,
            currency=user_obj.currency,
        )
        db.add(tx)
        await db.commit()
        await message.answer("✅ Transaction saved!", reply_markup=MAIN_MARKUP)
        await state.clear()


@router.message(F.text.lower() == "report")
async def report_handler(message: types.Message):
    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.telegram_chat_id == str(message.chat.id))
        )
        user = result.scalar_one()
        lang = user.language
        now = datetime.now()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        income = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user.id,
                Transaction.type == "income",
                Transaction.tx_date >= start,
            )
        )
        expense = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user.id,
                Transaction.type == "expense",
                Transaction.tx_date >= start,
            )
        )

        income_total = income.scalar() or 0
        expense_total = expense.scalar() or 0

        text = f"📊 Monthly Report:\n\nIncome: {income_total:.2f} {user.currency}\nExpense: {expense_total:.2f} {user.currency}"
        await message.answer(text, reply_markup=MAIN_MARKUP)


@router.message(F.text.lower() == "last transactions")
async def last_transactions_handler(message: types.Message, state: FSMContext):
    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.telegram_chat_id == str(message.chat.id))
        )
        user = result.scalar_one()

        transactions = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.tx_date.desc())
            .limit(5)
        )
        tx_list = transactions.scalars().all()

        if not tx_list:
            await message.answer("❌ No transactions found.")
            return

        smiles = {"income": "💰", "expense": "🧾"}

        text = "📝 Last 5 Transactions:\n"
        for tx in tx_list:
            text += f"{tx.tx_date.strftime('%Y-%m-%d')} 💵 {tx.amount} {tx.currency} {smiles[tx.type]} {tx.type} - {tx.category}\n"

        await message.answer(text, reply_markup=MAIN_MARKUP)
