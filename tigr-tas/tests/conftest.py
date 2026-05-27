import asyncio
import pytest
import pytest_asyncio
import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

# Set environment before importing app
import os
os.environ["APP_ENV"] = "testing"

from app.main import create_app
from app.config.settings import get_settings
from app.database.session import get_async_session
from app.database.base import Base

settings = get_settings()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        str(settings.database_url),
        echo=False,
        pool_size=5,
        max_overflow=10,
    )
    
    # Create tables
    async with engine.begin() as conn:
        # Since we use Alembic normally, in tests we can create tables directly
        # or rely on alembic being run before. Let's create directly for speed
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session_factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False,
        autocommit=False, autoflush=False
    )
    
    async with test_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested() # SAVEPOINT
        
        async_session = async_session_factory(bind=conn)
        
        # Override the dependency
        app = create_app()
        app.dependency_overrides[get_async_session] = lambda: async_session
        
        yield async_session
        
        # Cleanup
        await async_session.close()
        await conn.rollback()
        
@pytest_asyncio.fixture(scope="session")
async def test_app():
    app = create_app()
    yield app

@pytest_asyncio.fixture(scope="function")
async def async_client(test_app, db_session) -> AsyncGenerator[AsyncClient, None]:
    # We must apply dependency override here too if we want to use the session fixture
    test_app.dependency_overrides[get_async_session] = lambda: db_session
    
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
        
    test_app.dependency_overrides.clear()

@pytest.fixture
def fake_redis() -> fakeredis.aioredis.FakeRedis:
    return fakeredis.aioredis.FakeRedis(decode_responses=True)

@pytest.fixture
def sample_fasta_content() -> bytes:
    return b">gene_1\nATCGATCGATCGATCGATCG\n>gene_2\nGGCCTTAAGGCCTTAA\n"
