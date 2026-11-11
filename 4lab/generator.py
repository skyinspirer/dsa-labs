import random
from datetime import date, timedelta

import psycopg


import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://library:library@localhost:5432/library"
)

TITLES = [
    "Война и мир",
    "Преступление и наказание",
    "Мастер и Маргарита",
    "Отцы и дети",
    "Евгений Онегин",
    "Анна Каренина",
    "Идиот",
    "Дубровский",
]

AUTHORS = [
    "Лев Толстой",
    "Фёдор Достоевский",
    "Михаил Булгаков",
    "Иван Тургенев",
    "Александр Пушкин",
]

PUBLISHERS = [
    "Издательство 1",
    "Издательство 2",
    "Издательство 3",
]


def generate_books():
    rng = random.Random(42)
    books = []
    book_id = 1
    start_date = date(2026, 1, 1)

    for day_number in range(120):
        available_date = start_date + timedelta(days=day_number)

        for _ in range(13):
            books.append((
                book_id,
                rng.choice(TITLES),
                rng.choice(AUTHORS),
                rng.choice(PUBLISHERS),
                rng.randint(1950, 2025),
                round(rng.uniform(200, 3000), 2),
                available_date,
            ))
            book_id += 1

    return books


def main():
    books = generate_books()

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM books")

            cursor.executemany(
                """
                INSERT INTO books (
                    id, title, author, publisher,
                    published_year, price, available_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                books,
            )

    print(f"Добавлено книг: {len(books)}")


if __name__ == "__main__":
    main()