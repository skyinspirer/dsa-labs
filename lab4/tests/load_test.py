import argparse
import asyncio
import json
import random
import time
from statistics import median

import httpx


SEARCH_URL = "http://127.0.0.1:8000/search?origin=test&destination=test&date=2026-02-01"
HEALTH_URL = "http://127.0.0.1:8000/health"


def percentile(values, percent):
    if not values:
        return 0.0
    values = sorted(values)
    index = round((percent / 100) * (len(values) - 1))
    return values[index]


def print_stats(name, latencies, errors, elapsed):
    print(f"\n{name}")
    print(f"Запросов: {len(latencies) + errors}")
    print(f"Успешных ответов: {len(latencies)}")
    print(f"Ошибок: {errors}")
    print(f"Длительность: {elapsed:.2f} с")
    print(f"Запросов/с: {(len(latencies) + errors) / elapsed:.2f}")

    if latencies:
        print(f"p50: {percentile(latencies, 50):.3f} с")
        print(f"p95: {percentile(latencies, 95):.3f} с")
        print(f"p99: {percentile(latencies, 99):.3f} с")
        print(f"Максимум: {max(latencies):.3f} с")
        print(f"Медиана: {median(latencies):.3f} с")


async def send_search(client, latencies, error_counter):
    start = time.perf_counter()

    try:
        response = await client.get(SEARCH_URL, timeout=30)
        response.raise_for_status()
        latencies.append(time.perf_counter() - start)
    except Exception:
        error_counter[0] += 1


async def closed_loop(client, concurrency, duration, latencies, errors):
    deadline = time.perf_counter() + duration

    async def worker():
        while time.perf_counter() < deadline:
            await send_search(client, latencies, errors)

    await asyncio.gather(*(worker() for _ in range(concurrency)))


async def open_loop(client, rate, duration, latencies, errors):
    start = time.perf_counter()
    deadline = start + duration
    tasks = []

    while time.perf_counter() < deadline:
        tasks.append(
            asyncio.create_task(send_search(client, latencies, errors))
        )
        # Экспоненциальное время между запросами.
        await asyncio.sleep(random.expovariate(rate))

    await asyncio.gather(*tasks)


async def monitor_health(client, duration, health_latencies, health_errors):
    deadline = time.perf_counter() + duration

    while time.perf_counter() < deadline:
        start = time.perf_counter()

        try:
            response = await client.get(HEALTH_URL, timeout=2)
            response.raise_for_status()
            health_latencies.append(time.perf_counter() - start)
        except Exception:
            health_errors[0] += 1

        await asyncio.sleep(0.1)


async def main(args):
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        # Прогрев сервиса.
        for _ in range(5):
            try:
                await client.get(HEALTH_URL)
            except Exception:
                pass

        latencies = []
        errors = [0]
        health_latencies = []
        health_errors = [0]

        start = time.perf_counter()

        health_task = asyncio.create_task(
            monitor_health(
                client,
                args.duration,
                health_latencies,
                health_errors,
            )
        )

        if args.mode == "closed":
            await closed_loop(
                client, args.concurrency, args.duration, latencies, errors
            )
        else:
            await open_loop(
                client, args.rate, args.duration, latencies, errors
            )

        await health_task
        elapsed = time.perf_counter() - start

        print_stats("Поиск книг", latencies, errors[0], elapsed)
        print_stats(
            "Проверка /health",
            health_latencies,
            health_errors[0],
            elapsed,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["closed", "open"], default="closed")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--rate", type=float, default=5)
    parser.add_argument("--duration", type=int, default=60)
    args = parser.parse_args()

    asyncio.run(main(args))