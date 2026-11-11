from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from worker.database import Account, Operation, SessionLocal
from worker.domain import process_operation


async def process_operation_data(data: dict):
    async with SessionLocal() as session:
        async with session.begin():

            # Проверяем, не была ли операция уже обработана.
            existing_operation = await session.get(
                Operation,
                data["operation_id"]
            )

            if existing_operation:
                return {
                    "operation_id": existing_operation.operation_id,
                    "status": existing_operation.status,
                    "points_delta": existing_operation.points_delta,
                    "balance_after": existing_operation.balance_after,
                    "reject_reason": existing_operation.reject_reason
                }

            # Получаем бонусный счёт или создаём новый с нулевым балансом.
            account = await session.get(
                Account,
                data["customer_id"]
            )

            if account is None:
                account = Account(
                    customer_id=data["customer_id"],
                    balance=0
                )
                session.add(account)
                await session.flush()

            operation_type = data["type"]
            amount = (
                Decimal(str(data["amount"]))
                if data.get("amount") is not None
                else None
            )
            points = data.get("points")

            duplicate_purchase = False
            purchase_customer_id = None
            purchase_points = None
            already_returned = False

            # Проверяем исходную покупку при возврате.
            if operation_type == "return":

                purchase = await session.scalar(
                    select(Operation).where(
                        Operation.check_number == data["check_number"],
                        Operation.type == "purchase",
                        Operation.status == "applied"
                    )
                )

                if purchase is not None:
                    purchase_customer_id = purchase.customer_id
                    purchase_points = purchase.points_delta

                    returned = await session.scalar(
                        select(Operation).where(
                            Operation.check_number == data["check_number"],
                            Operation.type == "return",
                            Operation.status == "applied"
                        )
                    )

                    already_returned = returned is not None

            # Проверяем повторную покупку с тем же номером чека.
            if operation_type == "purchase":
                purchase = await session.scalar(
                    select(Operation).where(
                        Operation.check_number == data["check_number"],
                        Operation.type == "purchase",
                        Operation.status == "applied"
                    )
                )

                duplicate_purchase = purchase is not None

            # Выполняем расчёт по правилам предметной области.
            result = process_operation(
                operation_type=operation_type,
                balance=account.balance,
                amount=amount,
                points=points,
                duplicate_purchase=duplicate_purchase,
                purchase_customer_id=purchase_customer_id,
                purchase_points=purchase_points,
                already_returned=already_returned,
                customer_id=data["customer_id"]
            )

            # Сохраняем новый баланс.
            account.balance = result.balance_after

            occurred_at = data["occurred_at"]

            if isinstance(occurred_at, str):
                occurred_at = datetime.fromisoformat(
                    occurred_at.replace("Z", "+00:00")
                )

            # Сохраняем результат операции.
            operation = Operation(
                operation_id=data["operation_id"],
                type=operation_type,
                customer_id=data["customer_id"],
                store_id=data["store_id"],
                check_number=data["check_number"],
                amount=amount,
                points_delta=result.points_delta,
                balance_after=result.balance_after,
                status=result.status,
                reject_reason=result.reject_reason,
                occurred_at=occurred_at,
                processed_at=datetime.now(timezone.utc)
            )

            session.add(operation)

            return {
                "operation_id": data["operation_id"],
                "status": result.status,
                "points_delta": result.points_delta,
                "balance_after": result.balance_after,
                "reject_reason": result.reject_reason
            }
