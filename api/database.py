from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

DATABASE_URL = os.environ["DATABASE_URL"]

# create_async_engine is the async version of SQLAlchemy's engine
# pool_size: how many DB connections to keep open simultaneously
# max_overflow: how many extra connections allowed beyond pool_size under load
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=False,  # set True locally if you want to see raw SQL in terminal
)

# async_sessionmaker creates a factory for database sessions
# expire_on_commit=False means objects don't expire after a commit,
# which matters in async context where lazy loading doesn't work
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


# This is the dependency — FastAPI calls this for every request
# that needs a DB connection. The `yield` makes it a context manager:
# setup before yield, teardown after yield (even if the route throws)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session