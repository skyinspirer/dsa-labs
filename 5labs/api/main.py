import os
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, desc
import aio_pika

from schemas import (
    OperationIn,
    OperationAccepted,
    OperationResult,
    AccountOut,
    AccountOperation,
)

DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL")

app = FastAPI(title="Loyalty API")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

connection: Optional[aio_pika.RobustConnection] = None
channel: Optional[aio_pika.Channel] = None
exchange: Optional[aio_pika.Exchange] = None


@app.on_event("startup")
async def startup():
    global connection, channel, exchange
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel(
        publisher_confirms=True,
        on_return_raises=True,
    )
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


@app.on_event("shutdown")
async def shutdown():
    if connection:
        await connection.close()


@app.post(
    "/operations",
    response_model=OperationAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_operation(op: OperationIn):
    message = aio_pika.Message(
        body=op.model_dump_json().encode("utf-8"),
        content_type="application/json",
        message_id=op.operation_id,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )

    try:
        await exchange.publish(
            message,
            routing_key="operation",
            mandatory=True,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Брокер не подтвердил публикацию сообщения",
        )

    return OperationAccepted(operation_id=op.operation_id)


@app.get(
    "/operations/{operation_id}",
    response_model=OperationResult,
)
async def get_operation(operation_id: str):
    from worker.models import Operation

    async with async_session() as session:
        result = await session.execute(
            select(Operation).where(Operation.operation_id == operation_id)
        )
        op = result.scalar_one_or_none()

    if op is None:
        raise HTTPException(
            status_code=404,
            detail="Операция не найдена или ещё не обработана",
        )

    return OperationResult(
        operation_id=op.operation_id,
        status=op.status,
        points_delta=op.points_delta,
        balance_after=op.balance_after,
        reject_reason=op.reject_reason,
    )


@app.get(
    "/accounts/{customer_id}",
    response_model=AccountOut,
)
async def get_account(customer_id: str):
    from worker.models import Account, Operation

    async with async_session() as session:
        acc_result = await session.execute(
            select(Account).where(Account.customer_id == customer_id)
        )
        account = acc_result.scalar_one_or_none()
        if account is None:
            raise HTTPException(status_code=404, detail="Счёт покупателя не найден")

        ops_result = await session.execute(
            select(Operation)
            .where(Operation.customer_id == customer_id)
            .order_by(desc(Operation.processed_at))
            .limit(20)
        )
        ops = ops_result.scalars().all()

    return AccountOut(
        customer_id=account.customer_id,
        balance=account.balance,
        operations=[
            AccountOperation(
                operation_id=o.operation_id,
                type=o.type,
                store_id=o.store_id,
                check_number=o.check_number,
                points_delta=o.points_delta,
                balance_after=o.balance_after,
                status=o.status,
                reject_reason=o.reject_reason,
                processed_at=o.processed_at,
            )
            for o in ops
        ],
    )


@app.get("/health")
async def health():
    try:
        async with async_session() as session:
            await session.execute(select(1))

        if connection is None or connection.is_closed:
            raise RuntimeError("Соединение с RabbitMQ закрыто")

        return {"status": "ok"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис недоступен",
        )
