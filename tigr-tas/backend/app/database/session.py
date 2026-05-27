from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.engine import AsyncSessionLocal

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
