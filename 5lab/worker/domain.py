
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OperationResult:
    status: str
    points_delta: int
    balance_after: int
    reject_reason: str | None


def process_operation(
    operation_type: str,
    balance: int,
    amount: Decimal | None = None,
    points: int | None = None,
    duplicate_purchase: bool = False,
    purchase_customer_id: str | None = None,
    purchase_points: int | None = None,
    already_returned: bool = False,
    customer_id: str | None = None,
) -> OperationResult:

    # Покупка: начисляем 5% от суммы чека.
    if operation_type == "purchase":

        if duplicate_purchase:
            return OperationResult(
                "rejected", 0, balance, "duplicate_purchase"
            )

        accrued_points = int(amЫount * Decimal("0.05"))

        return OperationResult(
            "applied",
            accrued_points,
            balance + accrued_points,
            None
        )

    # Возврат: списываем все баллы, начисленные за покупку.
    elif operation_type == "return":

        if purchase_customer_id is None:
            return OperationResult(
                "rejected", 0, balance, "purchase_not_found"
            )

        if purchase_customer_id != customer_id:
            return OperationResult(
                "rejected", 0, balance, "customer_mismatch"
            )

        if already_returned:
            return OperationResult(
                "rejected", 0, balance, "already_returned"
            )

        deducted_points = purchase_points

        return OperationResult(
            "applied",
            -deducted_points,
            balance - deducted_points,
            None
        )

    # Оплата покупки бонусными баллами.
    elif operation_type == "redeem":

        if Decimal(points) > amount * Decimal("0.30"):
            return OperationResult(
                "rejected", 0, balance, "limit_exceeded"
            )

        if points > balance:
            return OperationResult(
                "rejected", 0, balance, "insufficient_balance"
            )

        return OperationResult(
            "applied",
            -points,
            balance - points,
            None
        )

    raise ValueError("Неизвестный тип операции")
