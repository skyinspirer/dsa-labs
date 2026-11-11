import os
import json
import asyncio
from decimal import Decimal
from datetime import datetime

import aio_pika
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from models import Base, Account, Operation
from domain import IncomingOperation, process_operation, get_customer_state, ProcessedOperation

DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_result(session: AsyncSession, result: ProcessedOperation, points: int | None):
    acc_result = await session.execute(
        select(Account).where(Account.customer_id == result.customer_id)
    )
    account = acc_result.scalar_one_or_none()
    if account is None:
        account = Account(customer_id=result.customer_id, balance=Decimal("0.00"))
        session.add(account)

    account.balance = result.balance_after

    op = Operation(
        operation_id=result.operation_id,
        type=result.type,
        customer_id=result.customer_id,
        store_id=result.store_id,
        check_number=result.check_number,
        amount=result.amount,
        points=points,
        points_delta=result.points_delta,
        balance_after=result.balance_after,
        status=result.status,
        reject_reason=result.reject_reason,
        occurred_at=result.occurred_at,
    )
    session.add(op)


async def handle_message(message: aio_pika.IncomingMessage):
    """Обработка одного сообщения (Задача 2.3)."""
    async with message.process():          # ACK только при успешном выходе
        data = json.loads(message.body.decode("utf-8"))

        op = IncomingOperation(
            operation_id=data["operation_id"],
            type=data["type"],
            customer_id=data["customer_id"],
            store_id=data["store_id"],
            check_number=data["check_number"],
            amount=Decimal(str(data["amount"])) if data.get("amount") is not None else None,
            points=data.get("points"),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

        async with async_session() as session:
            async with session.begin():     # одна транзакция
                hist_result = await session.execute(
                    select(Operation).where(Operation.customer_id == op.customer_id)
                )
                history_db = hist_result.scalars().all()

                history = [
                    ProcessedOperation(
                        operation_id=o.operation_id,
                        type=o.type,
                        customer_id=o.customer_id,
                        store_id=o.store_id,
                        check_number=o.check_number,
                        amount=o.amount,
                        points_delta=o.points_delta,
                        balance_after=o.balance_after,
                        status=o.status,
                        reject_reason=o.reject_reason,
                        occurred_at=o.occurred_at,
                    )
                    for o in history_db
                ]

                balance, _ = get_customer_state(op.customer_id, history)
                result = process_operation(op, balance, history)
                await save_result(session, result, op.points)

        print(
            f"Обработано: {result.operation_id} → {result.status} "
            f"(delta={result.points_delta}, balance={result.balance_after})"
        )


async def main():
    await init_db()
    print("Таблицы созданы / проверены")

    connection = await aio_pika.connect_robust(RABBITMQ_URL)  
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)               

        exchange = await channel.declare_exchange(
            "loyalty",
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )
        queue = await channel.declare_queue(
            "operations",
            durable=True,
            arguments={"x-queue-type": "quorum"},
        )
        await queue.bind(exchange, routing_key="operation")

        print("Worker запущен, ожидание сообщений")

        async with queue.iterator() as messages:
            async for message in messages:
                await handle_message(message)


if __name__ == "__main__":
    asyncio.run(main())
