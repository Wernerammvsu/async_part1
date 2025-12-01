"""
Сервисный уровень: orchestration.

Здесь:
- создание HTTP-сессии,
- управление пулом потоков,
- семафор для ограничения параллелизма,
- обработка всех тикеров.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import aiohttp

from . import config
from .tickers import ticker_generator
from . import moex_client
from . import storage

logger = logging.getLogger(__name__)


async def process_one_ticker(
    ticker: str,
    session: aiohttp.ClientSession,
    executor: ThreadPoolExecutor,
) -> None:
    """
    Обработка одного тикера:
        1. Получить дивиденды.
        2. Получить полную историю цен закрытия.
        3. Сохранить данные в CSV (через пул потоков).
    """
    logger.info(f"[{ticker}] Начало обработки тикера")

    try:
        dividends = await moex_client.fetch_dividends(session, ticker)
        history = await moex_client.fetch_full_history(session, ticker)

        loop = asyncio.get_running_loop()

        if dividends:
            await loop.run_in_executor(
                executor,
                storage.save_dividends_to_csv,
                ticker,
                dividends,
                config.OUTPUT_DIR,
            )
        else:
            logger.info(f"[{ticker}] Дивиденды не найдены, CSV не создаем.")

        if history:
            await loop.run_in_executor(
                executor,
                storage.save_prices_to_csv,
                ticker,
                history,
                config.OUTPUT_DIR,
            )
        else:
            logger.info(f"[{ticker}] История цен не найдена, CSV не создаем.")

        logger.info(f"[{ticker}] Обработка завершена успешно")

    except Exception as e:
        logger.exception(f"[{ticker}] Ошибка при обработке тикера: {e}")


async def run_all_tickers() -> None:
    """
    Основная точка входа асинхронного кода:
        - создает пул потоков,
        - создает HTTP-сессию aiohttp,
        - читает тикеры из файла,
        - ограничивает количество одновременных задач семафором,
        - ждет завершения всех задач.
    """
    executor = ThreadPoolExecutor(max_workers=config.MAX_WORKERS)
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)

    timeout = aiohttp.ClientTimeout(total=config.HTTP_TIMEOUT)
    headers = {"User-Agent": config.USER_AGENT}

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        tasks = []

        async for ticker in ticker_generator(config.TICKERS_FILE):
            ticker = ticker.strip().upper()
            if not ticker:
                continue

            async def sem_task(t: str) -> None:
                async with semaphore:
                    await process_one_ticker(t, session, executor)

            tasks.append(asyncio.create_task(sem_task(ticker)))

        if tasks:
            await asyncio.gather(*tasks)

    executor.shutdown(wait=True)
    logger.info("Все тикеры обработаны.")
