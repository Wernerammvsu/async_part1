"""
Модуль для работы со списком тикеров.

Задача: предоставить асинхронный генератор, который читает тикеры из файла.
"""

import asyncio
from pathlib import Path
from typing import AsyncIterator


async def ticker_generator(path: Path) -> AsyncIterator[str]:
    """
    Асинхронная функция-генератор, читающая тикеры из текстового файла.

    Формат файла:
        один тикер в строке, возможны пустые строки и пробелы.

    Пример содержимого:
        SBER
        GMKN
        LKOH

    Для учебных целей чтение файла выполнено синхронно, но добавлен
    await asyncio.sleep(0), чтобы сохранить асинхронность интерфейса
    и продемонстрировать async-генератор.
    """
    if not path.exists():
        raise FileNotFoundError(f"Файл с тикерами не найден: {path}")

    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        ticker = line.strip()
        if not ticker:
            continue

        # Уступаем управление циклу событий — хорошая практика
        # в асинхронных генераторах.
        await asyncio.sleep(0)
        yield ticker
