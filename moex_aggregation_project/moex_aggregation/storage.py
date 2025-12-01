"""
Модуль для сохранения данных в CSV.

Здесь — исключительно синхронные функции записи,
которые затем вызываются через run_in_executor.
"""

from pathlib import Path
from typing import Dict, List
import csv
import logging

logger = logging.getLogger(__name__)


def save_dividends_to_csv(
    ticker: str,
    records: List[Dict],
    output_dir: Path,
) -> Path:
    """
    Сохраняет дивиденды в CSV-файл <TICKER>_dividends.csv.

    Формат строк:
        date,value,currency
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
    records: List[Dict],
    output_dir: Path,
) -> Path:
    """
    Сохраняет историю цен закрытия в CSV-файл <TICKER>_prices.csv.

    Формат строк:
        date,close
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
