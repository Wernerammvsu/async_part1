"""
Точка входа командной строки.

Запуск:
    python run_aggregation.py
"""

import asyncio
import logging

from moex_aggregation.service import run_all_tickers


def setup_logging() -> None:
    """
    Простая базовая настройка логирования.
    В реальном проекте можно сделать конфиг через dictConfig / файл.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    setup_logging()
    try:
        asyncio.run(run_all_tickers())
    except KeyboardInterrupt:
        logging.getLogger(__name__).warning("Завершение по Ctrl+C")


if __name__ == "__main__":
    main()
