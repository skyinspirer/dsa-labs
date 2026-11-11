import json

import aio_pika

from worker.processor import process_operation_data

RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"

async def start_consumer():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    try:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

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

        await queue.bind(
            exchange,
            routing_key="operation"
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body.decode())
                    await process_operation_data(data)

    finally:
        await connection.close()
