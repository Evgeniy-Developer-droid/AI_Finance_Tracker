from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import os
from contextlib import asynccontextmanager


# Отримуємо URL до БД (можна з .env)
def get_database_url():
    # Спробуй взяти з env, або вкажи тут дефолт
    return os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://crm_user:crm_pass@localhost:5432/crm"
    )


DATABASE_URL = get_database_url()

# Створення асинхронного engine
engine = create_async_engine(DATABASE_URL, future=True, echo=False)

# Асинхронний sessionmaker
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session
