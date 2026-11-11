import asyncio

from worker.database import create_tables, close_database
from worker.consumer import start_consumer


async def main():
    await create_tables()

    try:
        await start_consumer()
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
