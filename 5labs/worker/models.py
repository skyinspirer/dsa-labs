from decimal import Decimal
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Numeric, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )


class Operation(Base):
    __tablename__ = "operations"

    operation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    store_id: Mapped[str] = mapped_column(String(32), nullable=False)
    check_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    points_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    reject_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )