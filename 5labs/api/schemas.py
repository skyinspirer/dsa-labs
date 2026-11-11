from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator


class OperationIn(BaseModel):
    operation_id: str = Field(..., min_length=1)
    type: Literal["purchase", "return", "redeem"]
    customer_id: str = Field(..., min_length=1)
    store_id: str = Field(..., min_length=1)
    check_number: str = Field(..., min_length=1)
    amount: Optional[Decimal] = None
    points: Optional[int] = None
    occurred_at: datetime

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v, info):
        op_type = info.data.get("type")
        if op_type in ("purchase", "redeem"):
            if v is None or v <= 0:
                raise ValueError("amount must be positive for purchase and redeem")
        if op_type == "return" and v is not None:
            raise ValueError("amount must be absent for return")
        return v

    @field_validator("points")
    @classmethod
    def points_rules(cls, v, info):
        op_type = info.data.get("type")
        if op_type == "redeem":
            if v is None or v <= 0:
                raise ValueError("points must be positive integer for redeem")
        if op_type in ("purchase", "return") and v is not None:
            raise ValueError("points must be absent for purchase and return")
        return v


class OperationAccepted(BaseModel):
    operation_id: str


class OperationResult(BaseModel):
    operation_id: str
    status: str
    points_delta: int
    balance_after: Decimal
    reject_reason: Optional[str] = None


class AccountOperation(BaseModel):
    operation_id: str
    type: str
    store_id: str
    check_number: str
    points_delta: int
    balance_after: Decimal
    status: str
    reject_reason: Optional[str] = None
    processed_at: datetime


class AccountOut(BaseModel):
    customer_id: str
    balance: Decimal
    operations: List[AccountOperation]
