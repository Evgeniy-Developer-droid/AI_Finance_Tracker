import os
import shutil
from uuid import uuid4
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Якщо треба підключати роутери — імпортуй тут:
from app.api.endpoints import auth, transactions
from app.tg_bot.webhook_router import router_webhook

app = FastAPI(title="AI Finance Tracker", version="0.1.0")

# CORS — дозволь localhost:3000 (Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # у production краще явно
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Базовий healthcheck
@app.get("/ping")
async def ping():
    return {"status": "ok"}


# Тут можна підключати роутери:
app.include_router(auth.router, prefix="/api/users", tags=["Users"])
app.include_router(
    transactions.router, prefix="/api/transactions", tags=["Transactions"]
)
app.include_router(router_webhook, tags=["Telegram Bot"])