from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://crm_user:crm_pass@db:5432/crm"
    )
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    SECRET_KEY: str = Field(default="super-secret")
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 365
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CURRENCY_CHOICES: List[str] = ["USD", "UAH"]
    CATEGORY_CHOICES_EXPENSE: List[str] = [
        "Food",
        "Transport",
        "Utilities",
        "Communication",
        "Entertainment",
        "Health",
        "Other",
    ]
    CATEGORY_CHOICES_INCOME: List[str] = [
        "Salary",
        "Business",
        "Investments",
        "Gifts",
        "Other",
    ]
    TELEGRAM_BOT_TOKEN: str = Field(default="123:ABC")
    TELEGRAM_WEBHOOK_SECRET: str = Field(default="supersecret123")
    SERVER_URL: str = Field(default="https://your-ngrok-url.ngrok.io")
    LIQPAY_PUBLIC_KEY: str = Field(default="your_public_key")
    LIQPAY_PRIVATE_KEY: str = Field(default="your_private_key")
    OPENAI_API_KEY: str = Field(default="your_openai_api_key")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
