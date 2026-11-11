CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(150) NOT NULL,
    publisher VARCHAR(100) NOT NULL,
    published_year INTEGER NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    available_date DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_books_available_date
ON books (available_date);