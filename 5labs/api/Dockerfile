FROM python:3.12-slim AS builder

WORKDIR /build
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

# создаём непривилегированного пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# копируем установленные пакеты из builder
COPY --from=builder /install /usr/local

# копируем код
COPY . .

# переключаемся на непривилегированного пользователя
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
