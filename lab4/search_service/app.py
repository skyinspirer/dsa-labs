
import os
import asyncio
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal

from concurrent.futures import ProcessPoolExecutor

import httpx
from fastapi import FastAPI, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://library:library@localhost:5432/library"
)

SUPPLIERS = [
    os.getenv("SUPPLIER_1_URL", "http://localhost:8001"),
    os.getenv("SUPPLIER_2_URL", "http://localhost:8002"),
    os.getenv("SUPPLIER_3_URL", "http://localhost:8003"),
]

REQUEST_TIMEOUT = 2.0
RETRY_DELAY = 0.2

process_pool = ProcessPoolExecutor(max_workers=2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
    app.state.http_client = httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT
    )


    try:
        app.state.process_pool = process_pool
        yield
    finally:    
        process_pool.shutdown(wait=True)
        await app.state.http_client.aclose()
        await app.state.engine.dispose()


app = FastAPI(
    title="Library Search Service",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


async def search_local_books(book_date: date):
    async with app.state.engine.connect() as connection:
        result = await connection.execute(
            text("""
                SELECT id, title, author, publisher,
                       published_year, price, available_date
                FROM books
                WHERE available_date = :book_date
            """),
            {"book_date": book_date},
        )
        rows = result.mappings().all()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "author": row["author"],
            "publisher": row["publisher"],
            "published_year": row["published_year"],
            "price": float(row["price"]),
            "available_date": row["available_date"].isoformat(),
            "source": "local",
        }
        for row in rows
    ]


async def get_supplier_books(url: str, book_date: date):
    client = app.state.http_client

    for attempt in range(2):
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await client.get(
                    f"{url}/books",
                    params={"date": book_date.isoformat()},
                )

            response.raise_for_status()
            data = response.json()

            books = data.get("books", [])
            for book in books:
                book["source"] = data.get("supplier", url)

            return books, None

        except (httpx.HTTPError, ValueError, TimeoutError) as error:
            if attempt == 0:
                await asyncio.sleep(RETRY_DELAY)
            else:
                return [], str(error)

    return [], "Неизвестная ошибка"


def combine_books(book_lists):
    unique = {}

    for books in book_lists:
        for book in books:
            key = (
                book.get("title", "").strip().lower(),
                book.get("author", "").strip().lower(),
                book.get("published_year"),
            )

            if key not in unique:
                unique[key] = book
            elif Decimal(str(book.get("price", 0))) < Decimal(
                str(unique[key].get("price", 0))
            ):
                unique[key] = book

    result = list(unique.values())
    result.sort(key=lambda book: float(book.get("price", 0)))
    return result[:20]


@app.get("/search")
async def search_books(
    origin: str = Query(default=""),
    destination: str = Query(default=""),
    date_value: date = Query(..., alias="date"),
):
    # Одновременно обращаемся к БД и всем поставщикам.
    results = await asyncio.gather(
        search_local_books(date_value),
        *[
            get_supplier_books(url, date_value)
            for url in SUPPLIERS
        ],
    )

    local_books = results[0]
    supplier_results = results[1:]

    all_books = [local_books]
    failed_suppliers = []
    successful_suppliers = 0

    for url, (books, error) in zip(SUPPLIERS, supplier_results):
        if error:
            failed_suppliers.append(url)
        else:
            successful_suppliers += 1
            all_books.append(books)

    loop = asyncio.get_running_loop()

    result = await loop.run_in_executor(
        app.state.process_pool,
        combine_books,
        all_books,
    )

    if not result and successful_suppliers == 0:
        return {
            "status": "temporarily_unavailable",
            "books": [],
            "failed_suppliers": failed_suppliers,
        }

    return {
        "status": "ok",
        "date": date_value.isoformat(),
        "count": len(result),
        "books": result,
        "failed_suppliers": failed_suppliers,
    }
