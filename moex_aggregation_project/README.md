\# Учебный проект: Агрегация рыночных данных (MOEX)



Проект демонстрирует получение исторических данных по акциям российских эмитентов

через ISS API Московской биржи с использованием асинхронного подхода (aiohttp).



\## Структура



\- `moex\_aggregation/` — пакет с логикой:

&nbsp; - `config.py` — настройки (пути, лимиты, User-Agent);

&nbsp; - `tickers.py` — асинхронный генератор тикеров;

&nbsp; - `moex\_client.py` — функции для работы с ISS API (дивиденды, история котировок);

&nbsp; - `storage.py` — функции сохранения в CSV;

&nbsp; - `service.py` — оркестрация: обработка всех тикеров.

\- `run\_aggregation.py` — точка входа.

\- `tickers.txt` — файл со списком тикеров (`SBER`, `GMKN`, ...).

\- `requirements.txt` — зависимости.



\## Установка и запуск



```bash

\# создать и активировать виртуальное окружение (рекомендуется)



pip install -r requirements.txt



\# создать файл tickers.txt (пример)

echo "SBER\\nGMKN\\nLKOH\\nMOEX\\nMGNT" > tickers.txt



\# запустить сбор данных

python run\_aggregation.py



По итогам работы в директории data/ будут созданы файлы:



<TICKER>\_dividends.csv



<TICKER>\_prices.csv





