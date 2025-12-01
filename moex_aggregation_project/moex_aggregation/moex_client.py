"""
Модуль для работы с ISS API Московской биржи.

Здесь нет логики сохранения — только HTTP-запросы и разбор JSON.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import aiohttp

from . import config

logger = logging.getLogger(__name__)


async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Выполняет GET-запрос и возвращает ответ в формате JSON (dict).

    При ошибочном статус-коде поднимает исключение aiohttp.ClientResponseError.
    """
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        data = await response.json()
        return data


async def fetch_dividends(
    session: aiohttp.ClientSession,
    ticker: str,
) -> List[Dict[str, Any]]:
    """
    Получает историю дивидендов по тикеру.

    Возвращаемый список словарей:
        {
            "date": "YYYY-MM-DD",
            "value": <float или None>,
            "currency": "RUB" и т.п.
        }
    """
    url = f"http://iss.moex.com/iss/securities/{ticker}/dividends.json"
    logger.info(f"[{ticker}] Запрос дивидендов: {url}")

    data = await fetch_json(session, url)
    div_section = data.get("dividends")

    if not div_section:
        logger.warning(f"[{ticker}] В ответе нет секции 'dividends'.")
        return []

    columns = div_section.get("columns", [])
    rows = div_section.get("data", [])

    if not rows:
        logger.info(f"[{ticker}] Дивиденды не найдены (пустой список data).")
        return []

    try:
        idx_date = columns.index("registryclosedate")
        idx_value = columns.index("value")
        idx_currency = columns.index("currencyid")
    except ValueError as e:
        logger.error(f"[{ticker}] Не найдены нужные колонки в dividends.columns: {e}")
        return []

    result: List[Dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "date": row[idx_date],
                "value": row[idx_value],
                "currency": row[idx_currency],
            }
        )

    return result


async def fetch_history_page(
    session: aiohttp.ClientSession,
    ticker: str,
    start: int = 0,
) -> List[Dict[str, Any]]:
    """
    Получает одну "страницу" истории котировок (до 100 записей) по тикеру,
    начиная с позиции 'start' (offset).

    Возвращает список словарей:
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
    params = {"start": start}

    logger.info(f"[{ticker}] Запрос истории цен, start={start}")
    data = await fetch_json(session, url, params=params)

    history = data.get("history")
    if not history:
        logger.warning(f"[{ticker}] В ответе нет секции 'history'.")
        return []

    columns = history.get("columns", [])
    rows = history.get("data", [])

    if not rows:
        # Больше данных нет
        return []

    try:
        idx_date = columns.index("TRADEDATE")
        idx_close = columns.index("CLOSE")
    except ValueError as e:
        logger.error(f"[{ticker}] Не найдены колонки TRADEDATE или CLOSE: {e}")
        return []

    result: List[Dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "date": row[idx_date],
                "close": row[idx_close],
            }
        )

    return result


async def fetch_full_history(
    session: aiohttp.ClientSession,
    ticker: str,
    page_size: int = config.HISTORY_PAGE_SIZE,
) -> List[Dict[str, Any]]:
    """
    Получает всю доступную историю котировок по тикеру,
    обходя ограничение API на количество записей в одном ответе.

    Стратегия:
        - запрашиваем страницы с параметром start: 0, 100, 200, ...
        - если страница вернула меньше page_size записей — это последняя.
    """
    all_records: List[Dict[str, Any]] = []

    start = 0
    while True:
        page = await fetch_history_page(session, ticker, start=start)
        if not page:
            break

        all_records.extend(page)

        if len(page) < page_size:
            break

        start += page_size

    logger.info(f"[{ticker}] Получено записей истории: {len(all_records)}")
    return all_records
