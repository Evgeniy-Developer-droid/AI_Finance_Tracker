import base64
from datetime import datetime, timedelta
import json
import uuid
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_current_user
from app.core.billing import (
    cancel_subscription,
    create_payment_data,
    generate_signature,
)
from app.db.session import get_db
from app.schemas import (
    AIGenerateInput,
    AnalyticsTransaction,
    AnalyticsTransactionForAI,
    CheckEmail,
    RegistrationInput,
    UserCreate,
    UserOut,
    UserUpdate,
    LoginInApp,
)
from app.models import Order, User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.config import settings
from app.crud import (
    create_order,
    get_order,
    get_transactions,
    get_user,
    get_user_by_email,
    create_user,
    update_user,
)

router = APIRouter()


@router.post("/signup", response_model=dict, status_code=201)
async def signup(user_in: RegistrationInput, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user_in.password)
    user_obj = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_subscribed=False,
        telegram_chat_id=None,
        currency=user_in.currency,
        language=user_in.language,
    )
    # Використовуємо CRUD create_user
    user = await create_user(db, user_obj)
    access_token = create_access_token(
        {"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "user": UserOut.model_validate(user),
        "access_token": access_token,
    }


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(
        {"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        {"sub": user.email},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login/app")
async def login_app(data: LoginInApp, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(
        {"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "user": UserOut.model_validate(user)}


@router.post("/refresh")
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    payload = decode_refresh_token(refresh_token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    new_access_token = create_access_token(
        {"sub": payload["sub"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_me(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    return user


@router.put("/me", response_model=UserOut)
async def update_me(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    update_data = user_in.model_dump(exclude_unset=True)
    user = await update_user(db, user.id, update_data)
    return user


@router.post("/check_email")
async def check_email(data: CheckEmail, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if user:
        return {"exists": True}
    return {"exists": False}


@router.post("/subscription/create-payment")
async def create_subscription_payment(
    description: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = Order(user_id=user.id, key=uuid.uuid4().hex)
    order = await create_order(db, order)

    payment_data = create_payment_data(
        amount=5.0,
        currency="USD",
        description=description or "Subscription Payment",
        order_id=order.key,
        result_url=f"{settings.SERVER_URL}/payment/result",
        server_url=f"{settings.SERVER_URL}/api/users/payment/webhook",
        language=user.language,
    )
    return payment_data


@router.post("/subscription/cancel")
async def cancel_subscription_api(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    result = cancel_subscription(user.order_id)
    return {"status": "success"}


@router.post("/payment/webhook")
async def payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    data = form.get("data")
    signature = form.get("signature")

    # перевірка підпису
    expected_signature = generate_signature(data)
    if signature != expected_signature:
        return {"status": "error", "message": "Invalid signature"}

    decoded_data = json.loads(base64.b64decode(data))
    print("Payment received:", decoded_data)

    status = decoded_data.get("status")
    action = decoded_data.get("action")
    order_id = decoded_data.get("order_id")
    order = await get_order(db, decoded_data.get("order_id"))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    user = await get_user(db, order.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if status == "subscribed" and action == "subscribe":

        data = {
            "is_subscribed": True,
            "subscription_start": datetime.fromtimestamp(
                decoded_data.get("create_date") / 1000
            ),
            "subscription_end": datetime.fromtimestamp(
                decoded_data.get("end_date") / 1000
            ),
            "subscription_id": decoded_data.get("liqpay_order_id"),
            "cancel_at_period_end": False,
            "liqpay_order_id": decoded_data.get("liqpay_order_id"),
            "order_id": decoded_data.get("order_id"),
        }
        await update_user(db, user.id, data)

    elif action in ["pay", "subscribe"] and status == "success":
        data = {
            "is_subscribed": True,
            "subscription_start": datetime.fromtimestamp(
                decoded_data.get("create_date") / 1000
            ),
            "subscription_end": datetime.fromtimestamp(
                decoded_data.get("end_date") / 1000
            ),
            "subscription_id": decoded_data.get("liqpay_order_id"),
            "cancel_at_period_end": False,
            "liqpay_order_id": decoded_data.get("liqpay_order_id"),
            "order_id": decoded_data.get("order_id"),
        }
        await update_user(db, user.id, data)

    elif action == "subscribe" and status == "unsubscribed":
        data = {
            "cancel_at_period_end": True,
        }
        await update_user(db, user.id, data)
        print(f"Підписка скасована: {order_id}, user: {user.id}")

    elif (action in ["pay", "subscribe"]) and status in [
        "failure",
        "error",
        "reversed",
    ]:
        data = {
            "is_subscribed": False,
            "subscription_id": decoded_data.get("liqpay_order_id"),
        }
        await update_user(db, user.id, data)

    else:
        print(f"Інший статус LiqPay: {decoded_data}")

    return {"status": status}


@router.post("/ai/generate")
async def generate_ai_response(
    data: AIGenerateInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.is_subscribed is False:
        text = (
            "Subscription required for AI features"
            if user.language == "en"
            else "Підписка потрібна для використання AI функцій"
        )
        return {"response": text}
    transactions = await get_transactions(
        db,
        user.id,
        start_date=datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ),
        end_date=datetime.now(),
        limit=10000,
    )
    transactions_dict = [
        AnalyticsTransactionForAI.model_validate(tx, by_alias=True).model_dump()
        for tx in transactions
    ]
    prompt = f"""
    You are a financial assistant. Based on the following transactions, answer the user's question.
    Transactions:
    {json.dumps(transactions_dict, indent=2)}
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.responses.create(
        model="gpt-4.1-mini", instructions=prompt, input=data.question
    )
    return {"response": response.output_text.replace("\n", " ").strip()}
