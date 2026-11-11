import os
import random
import time
from datetime import date

from fastapi import FastAPI, HTTPException, Query


app = FastAPI()

SUPPLIER_ID = int(os.getenv("SUPPLIER_ID", "1"))
AVG_DELAY_MS = int(os.getenv("AVG_DELAY_MS", "300"))
ERROR_RATE = float(os.getenv("ERROR_RATE", "0.05"))
SLOW_RATE = float(os.getenv("SLOW_RATE", "0"))
BOOKS_PER_DAY = int(os.getenv("BOOKS_PER_DAY", "500"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/books")
def get_books(book_date: date = Query(..., alias="date")):

    # Случайные события воспроизводятся для конкретной даты.
    seed = int(book_date.strftime("%Y%m%d")) + SUPPLIER_ID * 100000
    rng = random.Random(seed)

    if rng.random() < ERROR_RATE:
        raise HTTPException(status_code=500, detail="Ошибка поставщика")

    # Третий поставщик иногда отвечает с задержкой 3 секунды.
    if rng.random() < SLOW_RATE:
        time.sleep(3)
    else:
        delay = AVG_DELAY_MS * rng.uniform(0.7, 1.3)
        time.sleep(delay / 1000)

    books = []

    for number in range(BOOKS_PER_DAY):
        books.append({
            "id": f"{SUPPLIER_ID}-{book_date}-{number}",
            "title": f"Книга {number + 1}",
            "author": f"Автор {number % 50 + 1}",
            "publisher": f"Поставщик {SUPPLIER_ID}",
            "published_year": 1950 + number % 76,
            "price": round(200 + rng.random() * 2800, 2),
            "available_date": book_date.isoformat(),
        })

    return {
        "supplier": SUPPLIER_ID,
        "books": books,
    }