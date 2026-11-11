from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Optional, List
from datetime import datetime


@dataclass
class IncomingOperation:
    operation_id: str
    type: str                   
    customer_id: str
    store_id: str
    check_number: str
    amount: Optional[Decimal] = None
    points: Optional[int] = None
    occurred_at: datetime = None


@dataclass
class ProcessedOperation:
    operation_id: str
    type: str
    customer_id: str
    store_id: str
    check_number: str
    amount: Optional[Decimal]
    points_delta: int
    balance_after: Decimal
    status: str                  
    reject_reason: Optional[str]
    occurred_at: datetime


def process_operation(
    op: IncomingOperation,
    current_balance: Decimal,
    existing_operations: List[ProcessedOperation],
) -> ProcessedOperation:
    points_delta = 0
    status = "applied"
    reject_reason = None

    if op.type == "purchase":
        # Проверка дубликата покупки
        if any(
            o.type == "purchase"
            and o.check_number == op.check_number
            and o.status == "applied"
            for o in existing_operations
        ):
            status = "rejected"
            reject_reason = "duplicate_purchase"
        else:
            # Начисление 5 %, дробная часть отбрасывается
            points_delta = int(
                (op.amount * Decimal("0.05")).to_integral_value(rounding=ROUND_DOWN)
            )

    elif op.type == "return":
        # Ищем исходную принятую покупку
        purchase = next(
            (
                o for o in existing_operations
                if o.type == "purchase"
                and o.check_number == op.check_number
                and o.status == "applied"
            ),
            None,
        )

        if purchase is None:
            status = "rejected"
            reject_reason = "purchase_not_found"
        elif purchase.customer_id != op.customer_id:
            status = "rejected"
            reject_reason = "customer_mismatch"
        elif any(
            o.type == "return"
            and o.check_number == op.check_number
            and o.status == "applied"
            for o in existing_operations
        ):
            status = "rejected"
            reject_reason = "already_returned"
        else:
            # Списываем ровно те баллы, которые были начислены за покупку
            points_delta = -purchase.points_delta

    elif op.type == "redeem":
        # Лимит 30 % от суммы чека
        max_points = int(
            (op.amount * Decimal("0.30")).to_integral_value(rounding=ROUND_DOWN)
        )
        if op.points > max_points:
            status = "rejected"
            reject_reason = "limit_exceeded"
        elif op.points > current_balance:
            status = "rejected"
            reject_reason = "insufficient_balance"
        else:
            points_delta = -op.points

    else:
        status = "rejected"
        reject_reason = "invalid_type"

    if status == "rejected":
        points_delta = 0

    new_balance = current_balance + Decimal(points_delta)

    return ProcessedOperation(
        operation_id=op.operation_id,
        type=op.type,
        customer_id=op.customer_id,
        store_id=op.store_id,
        check_number=op.check_number,
        amount=op.amount,
        points_delta=points_delta,
        balance_after=new_balance,
        status=status,
        reject_reason=reject_reason,
        occurred_at=op.occurred_at,
    )


def get_customer_state(
    customer_id: str,
    all_operations: List[ProcessedOperation],
) -> tuple[Decimal, List[ProcessedOperation]]:
    customer_ops = [o for o in all_operations if o.customer_id == customer_id]
    balance = Decimal("0.00")
    for op in customer_ops:
        if op.status == "applied":
            balance += Decimal(op.points_delta)
    return balance, customer_ops
