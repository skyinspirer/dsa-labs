import os
import json
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal

import aio_pika
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, text

from api.database import (
    engine,
    SessionLocal,
    Account,
    Operation
)


RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://guest:guest@rabbitmq:5672/"
)

connection = None
channel = None
exchange = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global connection, channel, exchange

    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    channel = await connection.channel(
        publisher_confirms=True,
        on_return_raises=True
    )

    exchange = await channel.declare_exchange(
        "loyalty",
        aio_pika.ExchangeType.DIRECT,
        durable=True
    )

    queue = await channel.declare_queue(
        "operations",
        durable=True,
        arguments={"x-queue-type": "quorum"}
    )

    await queue.bind(exchange, routing_key="operation")

    yield

    await connection.close()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


class OperationRequest(BaseModel):
    operation_id: str
    type: str
    customer_id: str
    store_id: str
    check_number: str
    occurred_at: datetime
    amount: Decimal | None = None
    points: int | None = None

    @model_validator(mode="after")
    def validate_operation(self):
        if self.type not in ("purchase", "return", "redeem"):
            raise ValueError("Неизвестный тип операции")

        if self.type in ("purchase", "redeem"):
            if self.amount is None or self.amount <= 0:
                raise ValueError("Сумма должна быть положительной")

        if self.type == "redeem":
            if self.points is None or self.points <= 0:
                raise ValueError("Количество баллов должно быть положительным")

        if self.type != "redeem" and self.points is not None:
            raise ValueError("Поле points допустимо только для redeem")

        if self.type == "return" and self.amount is not None:
            raise ValueError("Для возврата поле amount не требуется")

        return self


@app.post("/operations", status_code=202)
async def create_operation(operation: OperationRequest):
    data = operation.model_dump(mode="json")

    message = aio_pika.Message(
        body=json.dumps(data).encode(),
        content_type="application/json",
        message_id=operation.operation_id,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )

    try:
        await exchange.publish(
            message,
            routing_key="operation",
            mandatory=True
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Не удалось отправить операцию в очередь"
        )

    return {
        "operation_id": operation.operation_id,
        "status": "accepted"
    }


@app.get("/operations/{operation_id}")
async def get_operation(operation_id: str):
    async with SessionLocal() as session:
        operation = await session.get(Operation, operation_id)

        if operation is None:
            raise HTTPException(
                status_code=404,
                detail="Операция ещё не обработана"
            )

        return {
            "operation_id": operation.operation_id,
            "status": operation.status,
            "points_delta": operation.points_delta,
            "balance_after": operation.balance_after,
            "reject_reason": operation.reject_reason
        }


@app.get("/accounts/{customer_id}")
async def get_account(customer_id: str):
    async with SessionLocal() as session:
        account = await session.get(Account, customer_id)

        if account is None:
            raise HTTPException(
                status_code=404,
                detail="Бонусный счёт не найден"
            )

        result = await session.scalars(
            select(Operation)
            .where(Operation.customer_id == customer_id)
            .order_by(Operation.processed_at.desc())
            .limit(20)
        )

        operations = result.all()

        return {
            "customer_id": customer_id,
            "balance": account.balance,
            "operations": [
                {
                    "operation_id": item.operation_id,
                    "type": item.type,
                    "status": item.status,
                    "points_delta": item.points_delta,
                    "balance_after": item.balance_after,
                    "reject_reason": item.reject_reason,
                    "processed_at": item.processed_at
                }
                for item in operations
            ]
        }


@app.get("/health")
async def health():
    try:
        async with engine.connect() as db_connection:
            await db_connection.execute(text("SELECT 1"))

        await channel.get_exchange("loyalty")

        return {"status": "ok"}

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database or RabbitMQ is unavailable"
        )
