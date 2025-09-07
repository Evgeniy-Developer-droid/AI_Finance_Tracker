import base64
from datetime import datetime
import json
import hashlib
import hmac
import os
from app.core.config import settings
import requests

LIQPAY_PUBLIC_KEY = settings.LIQPAY_PUBLIC_KEY
LIQPAY_PRIVATE_KEY = settings.LIQPAY_PRIVATE_KEY
API_URL = "https://www.liqpay.ua/api/request"


def generate_signature(data: str) -> str:
    return base64.b64encode(
        hashlib.sha1(
            f"{LIQPAY_PRIVATE_KEY}{data}{LIQPAY_PRIVATE_KEY}".encode()
        ).digest()
    ).decode()


def create_payment_data(
    amount: float,
    currency: str,
    description: str,
    order_id: str,
    result_url: str,
    server_url: str,
    language: str,
):
    payment_payload = {
        "public_key": LIQPAY_PUBLIC_KEY,
        "version": "3",
        "action": "subscribe",
        "amount": str(amount),
        "currency": currency,
        "description": description,
        "order_id": order_id,
        "language": language,
        "result_url": result_url,  # Куди користувача редіректне після оплати
        "server_url": server_url,  # Куди LiqPay надішле POST-запит з результатом
        "subscribe": "1",  # Підписка
        "subscribe_date_start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "subscribe_periodicity": "month",
    }

    data_json = json.dumps(payment_payload)
    data_encoded = base64.b64encode(data_json.encode()).decode()
    signature = generate_signature(data_encoded)

    return {"data": data_encoded, "signature": signature}


def cancel_subscription(order_id: str):
    payload = {
        "action": "unsubscribe",
        "version": 3,
        "public_key": LIQPAY_PUBLIC_KEY,
        "order_id": order_id,
    }

    json_str = json.dumps(payload, separators=(",", ":"))  # важливо: без пробілів
    data_encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    signature = generate_signature(data_encoded)

    response = requests.post(
        API_URL,
        data={
            "data": data_encoded,
            "signature": signature,
        },
    )
    return response.json()
