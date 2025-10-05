from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)