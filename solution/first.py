"""
Учебный проект: Агрегация рыночных данных
Часть 1. Получение исторических данных по тикерам и сохранение в CSV.

Что делает этот скрипт:

1. Читает список тикеров из файла tickers.txt (по одному в строке).
2. Для каждого тикера:
   - асинхронно запрашивает дивиденды через ISS API Московской биржи;
   - асинхронно запрашивает всю историю цен закрытия (CLOSE), обходя лимит 100 записей;
   - сохраняет данные в два CSV-файла:
       <TICKER>_dividends.csv
       <TICKER>_prices.csv
3. Для записи CSV использует пул потоков, чтобы не блокировать event loop.
"""

import asyncio
import csv
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp


# ------------------------- НАСТРОЙКИ ПРОЕКТА -------------------------

# Путь к файлу с тикерами
TICKERS_FILE = Path("tickers.txt")

# Директория, куда сохраняем CSV-файлы
OUTPUT_DIR = Path("data")

# Размер "страницы" истории котировок (API МОЕХ возвращает максимум 100 строк за запрос)
HISTORY_PAGE_SIZE = 100

# Максимальное количество одновременных запросов (простая защита от чрезмерной нагрузки)
MAX_CONCURRENT_REQUESTS = 5


# ------------------------- ЛОГИРОВАНИЕ -------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ------------------------- АСИНХРОННЫЙ ГЕНЕРАТОР ТИКЕРОВ -------------------------

async def ticker_generator(path: Path):
    """
    Асинхронная функция-генератор.
    Читает тикеры из текстового файла (по одному в строке) и выдает их по очереди.

    Здесь чтение делаем синхронно (файл небольшой), но добавляем await asyncio.sleep(0),
    чтобы это действительно был асинхронный генератор.
    """
    if not path.exists():
        raise FileNotFoundError(f"Файл с тикерами не найден: {path}")

    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        ticker = line.strip()
        if not ticker:
            continue
        # "уступаем" управление циклу событий, чтобы сохранить асинхронность
        await asyncio.sleep(0)
        yield ticker


# ------------------------- УТИЛИТЫ HTTP / JSON -------------------------

async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Выполняет GET-запрос и возвращает ответ в виде JSON (dict).
    При ошибочном статус-коде выбрасывает исключение.
    """
    async with session.get(url, params=params) as response:
        # Если статус не 200, это сразу ошибка
        response.raise_for_status()
        data = await response.json()
        return data


# ------------------------- ДИВИДЕНДЫ -------------------------

async def fetch_dividends(
    session: aiohttp.ClientSession,
    ticker: str,
) -> List[Dict[str, Any]]:
    """
    Получает историю дивидендов по тикеру.
    Возвращает список словарей вида:
    {
        "date": "YYYY-MM-DD",
        "value": <float> или <None>,
        "currency": "RUB" и т.п.
    }
    """
    url = f"http://iss.moex.com/iss/securities/{ticker}/dividends.json"
    logger.info(f"[{ticker}] Запрос дивидендов: {url}")

    data = await fetch_json(session, url)

    # В ответе ожидаем секцию "dividends"
    div_section = data.get("dividends")
    if not div_section:
        logger.warning(f"[{ticker}] Нет секции 'dividends' в ответе")
        return []

    columns = div_section.get("columns", [])
    rows = div_section.get("data", [])

    # Без данных просто возвращаем пустой список
    if not rows:
        logger.info(f"[{ticker}] Дивиденды не найдены (пустой список data).")
        return []

    # Ищем индексы интересующих колонок
    # Названия колонок можно посмотреть вручную в браузере.
    try:
        idx_date = columns.index("registryclosedate")  # дата закрытия реестра
        idx_value = columns.index("value")             # дивиденд на одну акцию
        idx_currency = columns.index("currencyid")     # валюта
    except ValueError as e:
        logger.error(f"[{ticker}] Не найдена одна из колонок в dividends.columns: {e}")
        return []

    result: List[Dict[str, Any]] = []
    for row in rows:
        # Некоторые значения могут быть None
        date = row[idx_date]
        value = row[idx_value]
        currency = row[idx_currency]

        result.append(
            {
                "date": date,
                "value": value,
                "currency": currency,
            }
        )

    return result


# ------------------------- ИСТОРИЯ КОТИРОВОК (ЦЕНЫ ЗАКРЫТИЯ) -------------------------

async def fetch_history_page(
    session: aiohttp.ClientSession,
    ticker: str,
    start: int = 0,
) -> List[Dict[str, Any]]:
    """
    Получает одну "страницу" истории котировок (до 100 записей) по тикеру,
    начиная с позиции 'start' (offset).
    Возвращает список словарей вида:
    {
        "date": "YYYY-MM-DD",
        "close": <float или None>,
    }
    """
    base_url = (
        "http://iss.moex.com/iss/history/engines/stock/"
        "markets/shares/boards/TQBR/securities/{ticker}.json"
    )
    url = base_url.format(ticker=ticker)

    params = {
        "start": start,  # смещение для пагинации
    }

    logger.info(f"[{ticker}] Запрос истории цен, start={start}")
    data = await fetch_json(session, url, params=params)

    history = data.get("history")
    if not history:
        logger.warning(f"[{ticker}] Нет секции 'history' в ответе")
        return []

    columns = history.get("columns", [])
    rows = history.get("data", [])

    if not rows:
        # Больше данных нет
        return []

    # Определяем индексы нужных колонок
    try:
        idx_date = columns.index("TRADEDATE")
        idx_close = columns.index("CLOSE")
    except ValueError as e:
        logger.error(f"[{ticker}] Не найдены колонки TRADEDATE или CLOSE: {e}")
        return []

    result: List[Dict[str, Any]] = []
    for row in rows:
        trade_date = row[idx_date]
        close_price = row[idx_close]
        result.append(
            {
                "date": trade_date,
                "close": close_price,
            }
        )

    return result


async def fetch_full_history(
    session: aiohttp.ClientSession,
    ticker: str,
    page_size: int = HISTORY_PAGE_SIZE,
) -> List[Dict[str, Any]]:
    """
    Получает всю доступную историю котировок по тикеру,
    постранично обходя ограничение в 100 записей.
    """
    all_records: List[Dict[str, Any]] = []

    start = 0
    while True:
        page = await fetch_history_page(session, ticker, start=start)
        if not page:
            break

        all_records.extend(page)

        # Если вернулось меньше, чем page_size записей, это последняя страница
        if len(page) < page_size:
            break

        start += page_size

    logger.info(f"[{ticker}] Получено записей истории: {len(all_records)}")
    return all_records


# ------------------------- ЗАПИСЬ В CSV (СИНХРОННЫЕ ФУНКЦИИ) -------------------------

def save_dividends_to_csv(
    ticker: str,
    records: List[Dict[str, Any]],
    output_dir: Path,
) -> Path:
    """
    Сохраняет дивиденды в CSV-файл вида <TICKER>_dividends.csv
    Формат: date,value,currency
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"{ticker}_dividends.csv"

    with filename.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "value", "currency"])
        for item in records:
            writer.writerow(
                [
                    item.get("date"),
                    item.get("value"),
                    item.get("currency"),
                ]
            )

    logger.info(f"[{ticker}] Дивиденды сохранены в {filename}")
    return filename


def save_prices_to_csv(
    ticker: str,
    records: List[Dict[str, Any]],
    output_dir: Path,
) -> Path:
    """
    Сохраняет историю цен закрытия в CSV-файл вида <TICKER>_prices.csv
    Формат: date,close
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"{ticker}_prices.csv"

    with filename.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "close"])
        for item in records:
            writer.writerow(
                [
                    item.get("date"),
                    item.get("close"),
                ]
            )

    logger.info(f"[{ticker}] История цен сохранена в {filename}")
    return filename


# ------------------------- ОБРАБОТКА ОДНОГО ТИКЕРА -------------------------

async def process_ticker(
    ticker: str,
    session: aiohttp.ClientSession,
    executor: ThreadPoolExecutor,
) -> None:
    """
    Основной сценарий для одного тикера:
    1. Получить дивиденды.
    2. Получить полную историю цен закрытия.
    3. Сохранить оба набора данных в CSV (в отдельном потоке).
    """
    logger.info(f"[{ticker}] Начало обработки тикера")

    try:
        dividends = await fetch_dividends(session, ticker)
        history = await fetch_full_history(session, ticker)

        # Для записи файлов используем run_in_executor, чтобы не блокировать event loop.
        loop = asyncio.get_running_loop()

        if dividends:
            await loop.run_in_executor(
                executor, save_dividends_to_csv, ticker, dividends, OUTPUT_DIR
            )
        else:
            logger.info(f"[{ticker}] Дивидендов нет, файл не создается.")

        if history:
            await loop.run_in_executor(
                executor, save_prices_to_csv, ticker, history, OUTPUT_DIR
            )
        else:
            logger.info(f"[{ticker}] История цен пуста, файл не создается.")

        logger.info(f"[{ticker}] Обработка завершена")

    except Exception as e:
        logger.exception(f"[{ticker}] Ошибка при обработке тикера: {e}")


# ------------------------- ОСНОВНАЯ ФУНКЦИЯ -------------------------

async def main():
    """
    1. Создает HTTP-сессию aiohttp.
    2. Читает тикеры из файла асинхронным генератором.
    3. Создает задачи для каждого тикера.
    4. Ограничивает количество одновременных запросов семафором.
    """
    # Пул потоков для записи CSV
    executor = ThreadPoolExecutor(max_workers=4)

    # Семафор для ограничения числа параллельных "процессов тикеров"
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    # Готовим HTTP-сессию
    timeout = aiohttp.ClientTimeout(total=60)  # общий таймаут на запрос
    headers = {
        # Некоторые сервисы могут не любить "пустой" User-Agent.
        "User-Agent": "AsyncMoexClient/1.0 (educational project)",
    }

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        tasks = []

        # Читаем тикеры из файла
        async for ticker in ticker_generator(TICKERS_FILE):
            ticker = ticker.strip().upper()
            if not ticker:
                continue

            # Оборачиваем обработку в семафор, чтобы не превышать лимит параллелизма
            async def sem_task(t: str):
                async with semaphore:
                    await process_ticker(t, session, executor)

            tasks.append(asyncio.create_task(sem_task(ticker)))

        # Ждем выполнения всех задач
        if tasks:
            await asyncio.gather(*tasks)

    # Завершаем пул потоков
    executor.shutdown(wait=True)
    logger.info("Все тикеры обработаны.")


# ------------------------- ТОЧКА ВХОДА -------------------------

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Остановка по Ctrl+C")
