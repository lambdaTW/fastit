import functools

import fastapi
from sqlalchemy import orm
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
from sqlalchemy import pool

from core import config

engine = None


@functools.lru_cache()
def get_settings() -> config.Settings:
    return config.Settings()


def get_db_engine(
    settings: config.Settings = fastapi.Depends(get_settings),
) -> sqlalchemy_asyncio.AsyncEngine:
    global engine
    engine = engine or sqlalchemy_asyncio.create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        poolclass=pool.NullPool,
    )
    return engine


def get_async_session_class(
    engine: sqlalchemy_asyncio.AsyncEngine = fastapi.Depends(get_db_engine),
) -> sqlalchemy_asyncio.AsyncSession:
    return orm.sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=sqlalchemy_asyncio.AsyncSession,
    )


async def get_db(
    async_session: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(
        get_async_session_class
    ),
) -> sqlalchemy_asyncio.AsyncSession:
    async with async_session() as session:
        yield session
