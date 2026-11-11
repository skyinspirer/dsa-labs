
import os

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    DateTime,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/loyalty"
)

engine = create_async_engine(DATABASE_URL)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    customer_id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    balance: Mapped[int] = mapped_column(
        Integer,
        default=0
    )


class Operation(Base):
    __tablename__ = "operations"

    operation_id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    type: Mapped[str] = mapped_column(String)
    customer_id: Mapped[str] = mapped_column(String)
    store_id: Mapped[str] = mapped_column(String)
    check_number: Mapped[str] = mapped_column(String)

    amount: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    points_delta: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String)
    reject_reason: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    occurred_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[object] = mapped_column(DateTime(timezone=True))


async def create_tables():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def close_database():
    await engine.dispose()
