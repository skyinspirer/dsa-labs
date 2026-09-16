
#  1 (builder): установка зависимостей

FROM python:3.11-slim AS builder

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt



#  2 (runtime): только код приложения + зависимости

FROM python:3.11-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /install /usr/local

COPY . .

EXPOSE 5000

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]