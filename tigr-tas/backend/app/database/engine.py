from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.config.settings import get_settings

settings = get_settings()

async_engine = create_async_engine(
    str(settings.database_url),
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=__import__('sqlalchemy.ext.asyncio').ext.asyncio.AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
