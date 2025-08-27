from fastapi import APIRouter, Request
from aiogram import types
from httpcore import request
from app.tg_bot.bot import bot, dp
from app.tg_bot.handlers import router
from app.core.config import settings


router_webhook = APIRouter()
dp.include_router(router)


@router_webhook.post(f"/webhook/{settings.TELEGRAM_WEBHOOK_SECRET}")
async def telegram_webhook(request: Request):
    body = await request.json()
    update = types.Update(**body)
    await dp.feed_update(bot, update)
    return {"ok": True}
