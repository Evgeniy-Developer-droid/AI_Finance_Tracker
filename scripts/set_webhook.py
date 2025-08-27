import asyncio
from aiogram import Bot
from app.core.config import settings

#  sudo docker exec backend python -m scripts.set_webhook


async def set_webhook():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    webhook_url = f"{settings.SERVER_URL}/webhook/{settings.TELEGRAM_WEBHOOK_SECRET}"
    await bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set to: {webhook_url}")


if __name__ == "__main__":
    asyncio.run(set_webhook())
