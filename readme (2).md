\# Учебный проект: агрегация рыночных данных  

\## Часть 1. Получение исторических данных и сохранение в файлы



\## 1. Сюжет и цель проекта



Правительство РФ заявило цель — \*\*удвоить капитализацию фондового рынка к 2030 году\*\*. В рамках этой инициативы Центральный Банк и Минфин продвигают идею долгосрочных частных инвестиций и поддерживают развитие информационных сервисов.



Представьте, что вы работаете в стартапе, который хочет участвовать в этой программе. Заказчик (ЦБ) хочет \*\*демо-сервис\*\*, который наглядно показывает преимущества регулярного и долгосрочного инвестирования в российские акции.



В рамках проекта вы:



1\. Получаете \*\*исторические рыночные данные\*\* (цены и дивиденды) по выбранным акциям.

2\. Сохраняете данные в удобном формате (CSV).

3\. Далее будете моделировать стратегии инвестирования (в следующих частях проекта).



В этой первой части вы сосредотачиваетесь только на \*\*получении и сохранении данных\*\*.



---



\## 2. Задача первой части



\*\*Цель:\*\*  

написать программу, которая:



1\. Читает список тикеров российских компаний из текстового файла.

2\. Для каждого тикера:

&nbsp;  - получает историю котировок (цены закрытия по дням);

&nbsp;  - получает историю дивидендных выплат;

&nbsp;  - сохраняет обе истории в \*\*отдельные CSV-файлы\*\*.



\*\*Требования по реализации:\*\*



\- Для чтения тикеров из файла — использовать \*\*асинхронную функцию-генератор\*\*.

\- Для запросов к API Московской биржи в финальном решении — использовать \*\*асинхронный код\*\* (например, с `aiohttp`).

\- В учебных целях можно сначала написать \*\*синхронный пример с `requests`\*\* (он проще для понимания).

\- В конце работы у вас для каждого тикера должно быть \*\*два CSV-файла\*\*:

&nbsp; - `…\_prices.csv` — дата и цена закрытия.

&nbsp; - `…\_dividends.csv` — дата и выплата на одну акцию.



Тестирующей системы нет — важен \*\*рабочий код\*\* и \*\*понятная структура\*\*.



---



\## 3. Базовая теория



\### 3.1. Что такое тикер



\*\*Тикер\*\* — это краткое буквенное обозначение ценной бумаги на бирже. Например:



\- `SBER` — Сбербанк (обычные акции)  

\- `SBERP` — Сбербанк (привилегированные акции)  

\- `GMKN` — ГМК «Норильский никель»  

\- `LKOH` — Лукойл  

\- `MOEX` — Московская биржа  



Короткое видео по теме (по желанию):  

\*\*«Что такое тикер?»\*\* — Андрей Марков, «Хулиномика»  

<https://youtu.be/WCMosPVeMgQ>



---



\### 3.2. Обзор API Московской биржи (ISS)



Московская биржа предоставляет публичный HTTP-интерфейс \*\*ISS API\*\*.  

Нас будут интересовать три типа запросов:



1\. \*\*Дивиденды по бумаге:\*\*



&nbsp;  ```text

&nbsp;  http://iss.moex.com/iss/securities/{TICKER}/dividends.json

````



Пример:



```text

http://iss.moex.com/iss/securities/GMKN/dividends.json

```



2\. \*\*История котировок (цены):\*\*



&nbsp;  ```text

&nbsp;  http://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/{TICKER}.json

&nbsp;  ```



&nbsp;  Можно добавить параметры:



&nbsp;  ```text

&nbsp;  ?from=YYYY-MM-DD\&till=YYYY-MM-DD

&nbsp;  ```



&nbsp;  Пример:



&nbsp;  ```text

&nbsp;  http://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/GMKN.json?from=2023-05-25\&till=2023-05-27

&nbsp;  ```



&nbsp;  \*\*Ограничение:\*\*

&nbsp;  один ответ содержит \*\*не более 100 котировок\*\* (100 торговых дней).

&nbsp;  Для получения всей истории нужно будет \*\*перелистывать страницы\*\* (позже вы придумаете стратегию).



3\. \*\*Доступные границы истории котировок:\*\*



&nbsp;  ```text

&nbsp;  http://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/{TICKER}/dates.json

&nbsp;  ```



&nbsp;  Это простой ответ с \*\*минимальной и максимальной датой\*\*, за которые доступны котировки.



---



\### 3.3. Формат ответа: JSON



Все эти запросы возвращают данные в формате \*\*JSON\*\* — это стандартный текстовый формат обмена данными (очень удобен для работы в Python).



Типичная структура ответа (упрощённо, для понимания):



```json

{

&nbsp; "dividends": {

&nbsp;   "columns": \["SECID", "ISIN", "registryclosedate", "value", "currencyid"],

&nbsp;   "data": \[

&nbsp;     \["GMKN", "RU0007288411", "2013-11-01", 220.7, "RUB"],

&nbsp;     \["GMKN", "RU0007288411", "2014-06-30", 248.0, "RUB"]

&nbsp;   ]

&nbsp; }

}

```



Т.е. есть:



\* массив `columns` — \*\*названия столбцов\*\*;

\* массив `data` — список строк, каждая строка — список значений.



В истории котировок похожая структура, только секция будет называться `history`, а в `columns` будут, например, такие имена:



\* `TRADEDATE` — дата торгов,

\* `CLOSE` — цена закрытия,

\* и другие поля.



---



\## 4. Как посмотреть данные через браузер



\### 4.1. Дивиденды



1\. Откройте браузер.



2\. В адресную строку вставьте:



&nbsp;  ```text

&nbsp;  http://iss.moex.com/iss/securities/GMKN/dividends.json

&nbsp;  ```



3\. Нажмите Enter.



Браузер либо:



\* покажет JSON «как есть»,

\* либо предложит его скачать,

\* либо потребуется плагин, чтобы красиво отобразить JSON.



Обратите внимание на:



\* массив `columns` — какие есть поля;

\* массив `data` — как выглядят строки данных.



---



\### 4.2. История цен



Вставьте в браузер:



```text

http://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/GMKN.json?from=2023-05-25\&till=2023-05-27

```



Посмотрите секцию `history`:



\* `columns` — имена столбцов (ищите `TRADEDATE` и `CLOSE`);

\* `data` — строки, где в каждой строке одно из полей — цена закрытия.



---



\### 4.3. Границы дат



Проверьте:



```text

http://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/GMKN/dates.json

```



Здесь вы увидите \*\*две даты\*\* — начало и конец доступной истории торгов по данной бумаге.



---



\## 5. Подготовка файла с тикерами



Создайте обычный текстовый файл, например `tickers.txt`.

Поместите туда \*\*4–5 тикеров\*\* на свой вкус (по одному в строке). Например:



```text

SBER

GMKN

LKOH

MOEX

MGNT

```



Рекомендуется выбрать компании из разных отраслей (банки, нефть/газ, металлургия, ритейл и т.д.), чтобы позже демонстрировать идею диверсификации.



---



\## 6. Как работать с JSON в Python



В Python есть стандартный модуль `json`. Но чаще всего при работе с HTTP-библиотеками (например, `requests` или `aiohttp`) JSON уже автоматически преобразуется в \*\*словарь (`dict`)\*\* и списки (`list`).



Пример использования «чистого» `json`:



```python

import json



raw\_text = '''

{

&nbsp; "example": {

&nbsp;   "columns": \["A", "B"],

&nbsp;   "data": \[\[1, 2], \[3, 4]]

&nbsp; }

}

'''



data = json.loads(raw\_text)     # превращаем текст в dict

example = data\["example"]



columns = example\["columns"]    # \["A", "B"]

rows = example\["data"]          # \[\[1, 2], \[3, 4]]



print(columns)

print(rows)

```



С ISS API всё примерно так же, только вместо `json.loads` мы будем использовать метод `.json()`, предоставляемый HTTP-клиентом.



---



\## 7. Синхронный пример: получение данных с `requests`



Начнём с \*\*простого и понятного\*\* варианта — синхронного кода на основе библиотеки \[`requests`](https://requests.readthedocs.io/).



> В финальном решении проекта нужно будет использовать \*\*асинхронный вариант\*\*, но синхронный пример поможет понять структуру данных и шаги решения.



\### 7.1. Установка библиотеки



```bash

pip install requests

```



\### 7.2. Пример: дивиденды по одному тикеру



```python

import requests



def fetch\_dividends(ticker: str) -> list\[dict]:

&nbsp;   """

&nbsp;   Запрашивает историю дивидендов по тикеру и

&nbsp;   возвращает список словарей: {"date": ..., "value": ..., "currency": ...}

&nbsp;   """

&nbsp;   url = f"http://iss.moex.com/iss/securities/{ticker}/dividends.json"

&nbsp;   response = requests.get(url)

&nbsp;   response.raise\_for\_status()        # выбросит исключение, если статус != 200



&nbsp;   data = response.json()             # dict со всей структурой JSON

&nbsp;   div\_section = data\["dividends"]    # секция с дивидендами

&nbsp;   columns = div\_section\["columns"]   # список названий колонок

&nbsp;   rows = div\_section\["data"]         # список строк



&nbsp;   # Находим индексы нужных колонок

&nbsp;   idx\_date = columns.index("registryclosedate")

&nbsp;   idx\_value = columns.index("value")

&nbsp;   idx\_currency = columns.index("currencyid")



&nbsp;   # Преобразуем строки в удобный формат

&nbsp;   result = \[]

&nbsp;   for row in rows:

&nbsp;       item = {

&nbsp;           "date": row\[idx\_date],       # строка 'YYYY-MM-DD'

&nbsp;           "value": row\[idx\_value],     # число (дивиденд на одну акцию)

&nbsp;           "currency": row\[idx\_currency]

&nbsp;       }

&nbsp;       result.append(item)



&nbsp;   return result





if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   dividends = fetch\_dividends("GMKN")

&nbsp;   for item in dividends\[:5]:  # выведем первые 5 записей

&nbsp;       print(item)

```



---



\### 7.3. Пример: история цен (цены закрытия)



```python

import requests



def fetch\_history\_close\_prices(ticker: str, date\_from: str | None = None, date\_till: str | None = None) -> list\[dict]:

&nbsp;   """

&nbsp;   Запрашивает историю котировок по тикеру (цены закрытия).

&nbsp;   Можно указать границы дат в формате 'YYYY-MM-DD'.

&nbsp;   Возвращает список словарей: {"date": ..., "close": ...}

&nbsp;   """

&nbsp;   base\_url = (

&nbsp;       "http://iss.moex.com/iss/history/engines/stock/"

&nbsp;       "markets/shares/boards/TQBR/securities/{ticker}.json"

&nbsp;   )



&nbsp;   params = {}

&nbsp;   if date\_from is not None:

&nbsp;       params\["from"] = date\_from

&nbsp;   if date\_till is not None:

&nbsp;       params\["till"] = date\_till



&nbsp;   url = base\_url.format(ticker=ticker)



&nbsp;   response = requests.get(url, params=params)

&nbsp;   response.raise\_for\_status()



&nbsp;   data = response.json()

&nbsp;   history = data\["history"]

&nbsp;   columns = history\["columns"]

&nbsp;   rows = history\["data"]



&nbsp;   idx\_date = columns.index("TRADEDATE")

&nbsp;   idx\_close = columns.index("CLOSE")



&nbsp;   result = \[]

&nbsp;   for row in rows:

&nbsp;       item = {

&nbsp;           "date": row\[idx\_date],    # 'YYYY-MM-DD'

&nbsp;           "close": row\[idx\_close],  # цена закрытия

&nbsp;       }

&nbsp;       result.append(item)



&nbsp;   return result





if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   prices = fetch\_history\_close\_prices("GMKN", date\_from="2023-05-25", date\_till="2023-05-27")

&nbsp;   for p in prices:

&nbsp;       print(p)

```



> \*\*Замечание:\*\*

> здесь мы пока \*\*игнорируем ограничение в 100 записей\*\*. В реальном решении вам нужно будет обработать \*\*всю историю\*\*, перелистывая страницы (например, с помощью параметра `start` или перебора диапазонов дат).



---



\### 7.4. Простейшая запись в CSV



Для записи в CSV можно использовать стандартный модуль `csv`:



```python

import csv



def save\_dividends\_to\_csv(ticker: str, records: list\[dict], filename: str | None = None) -> None:

&nbsp;   """

&nbsp;   Сохраняет дивиденды в CSV-файл.

&nbsp;   Формат: date,value,currency

&nbsp;   """

&nbsp;   if filename is None:

&nbsp;       filename = f"{ticker}\_dividends.csv"



&nbsp;   with open(filename, "w", newline="", encoding="utf-8") as f:

&nbsp;       writer = csv.writer(f)

&nbsp;       writer.writerow(\["date", "value", "currency"])  # заголовок



&nbsp;       for item in records:

&nbsp;           writer.writerow(\[item\["date"], item\["value"], item\["currency"]])





def save\_prices\_to\_csv(ticker: str, records: list\[dict], filename: str | None = None) -> None:

&nbsp;   """

&nbsp;   Сохраняет цены закрытия в CSV-файл.

&nbsp;   Формат: date,close

&nbsp;   """

&nbsp;   if filename is None:

&nbsp;       filename = f"{ticker}\_prices.csv"



&nbsp;   with open(filename, "w", newline="", encoding="utf-8") as f:

&nbsp;       writer = csv.writer(f)

&nbsp;       writer.writerow(\["date", "close"])



&nbsp;       for item in records:

&nbsp;           writer.writerow(\[item\["date"], item\["close"]])





if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   from pprint import pprint



&nbsp;   dividends = fetch\_dividends("GMKN")

&nbsp;   save\_dividends\_to\_csv("GMKN", dividends)



&nbsp;   prices = fetch\_history\_close\_prices("GMKN", date\_from="2023-01-01", date\_till="2023-12-31")

&nbsp;   save\_prices\_to\_csv("GMKN", prices)



&nbsp;   print("Готово! Файлы GMKN\_dividends.csv и GMKN\_prices.csv созданы.")

```



---



\## 8. Асинхронный подход: набросок решения с `aiohttp`



Синхронный код прост, но \*\*плохо масштабируется\*\*, когда нужно:



\* отправить много запросов (по нескольким тикерам),

\* перелистывать страницы истории,

\* по возможности не блокировать поток исполнения.



В финальном решении \*\*обязательно\*\* используйте \*\*асинхронный вариант\*\*. Один из самых популярных инструментов — библиотека \[`aiohttp`](https://docs.aiohttp.org/).



\### 8.1. Установка aiohttp



```bash

pip install aiohttp

```



---



\### 8.2. Асинхронная функция-генератор для чтения тикеров



```python

import asyncio

from pathlib import Path



async def ticker\_generator(path: str):

&nbsp;   """

&nbsp;   Асинхронная функция-генератор.

&nbsp;   Построчно читает файл с тикерами и выдаёт (yield) по одному тикеру.

&nbsp;   Для простоты используем синхронное чтение, оно всё равно быстрое.

&nbsp;   """

&nbsp;   # Здесь могли бы использовать aiofiles, но для небольшого файла это не критично.

&nbsp;   for line in Path(path).read\_text(encoding="utf-8").splitlines():

&nbsp;       ticker = line.strip()

&nbsp;       if ticker:

&nbsp;           # имитируем асинхронность, чтобы показать, что это async-генератор

&nbsp;           await asyncio.sleep(0)

&nbsp;           yield ticker





async def demo():

&nbsp;   async for ticker in ticker\_generator("tickers.txt"):

&nbsp;       print("Тикер из файла:", ticker)





if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   asyncio.run(demo())

```



---



\### 8.3. Асинхронный запрос JSON с `aiohttp`



```python

import asyncio

import aiohttp



async def fetch\_json(session: aiohttp.ClientSession, url: str, params: dict | None = None) -> dict:

&nbsp;   """

&nbsp;   Асинхронно выполняет GET запрос и возвращает JSON как dict.

&nbsp;   """

&nbsp;   async with session.get(url, params=params) as response:

&nbsp;       response.raise\_for\_status()

&nbsp;       return await response.json()

```



---



\### 8.4. Асинхронный запрос дивидендов



```python

async def fetch\_dividends\_async(session: aiohttp.ClientSession, ticker: str) -> list\[dict]:

&nbsp;   url = f"http://iss.moex.com/iss/securities/{ticker}/dividends.json"

&nbsp;   data = await fetch\_json(session, url)



&nbsp;   div\_section = data\["dividends"]

&nbsp;   columns = div\_section\["columns"]

&nbsp;   rows = div\_section\["data"]



&nbsp;   idx\_date = columns.index("registryclosedate")

&nbsp;   idx\_value = columns.index("value")

&nbsp;   idx\_currency = columns.index("currencyid")



&nbsp;   result = \[]

&nbsp;   for row in rows:

&nbsp;       result.append({

&nbsp;           "date": row\[idx\_date],

&nbsp;           "value": row\[idx\_value],

&nbsp;           "currency": row\[idx\_currency],

&nbsp;       })

&nbsp;   return result

```



---



\### 8.5. Пример асинхронного `main`



Это лишь \*\*набросок\*\*, не финальное решение:



```python

async def main():

&nbsp;   async with aiohttp.ClientSession() as session:

&nbsp;       async for ticker in ticker\_generator("tickers.txt"):

&nbsp;           print(f"Обрабатываем {ticker}...")

&nbsp;           dividends = await fetch\_dividends\_async(session, ticker)

&nbsp;           # здесь можно вызвать синхронную функцию записи в CSV,

&nbsp;           # либо вынести запись в отдельный поток (ThreadPoolExecutor)

&nbsp;           # save\_dividends\_to\_csv(ticker, dividends)



if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   asyncio.run(main())

```



В дальнейшем вы сможете:



\* запускать \*\*несколько запросов одновременно\*\* с помощью `asyncio.gather`;

\* использовать \*\*пул потоков\*\* для записи больших файлов, чтобы не блокировать event loop;

\* добавить логику \*\*пагинации\*\* для получения всей истории котировок.



---



\## 9. Формулировка задания для самостоятельной работы



\*\*Ваша задача в первой части проекта — реализовать следующий функционал:\*\*



1\. \*\*Файл с тикерами:\*\*



&nbsp;  \* Создайте текстовый файл `tickers.txt`.

&nbsp;  \* Поместите туда 4–5 тикеров российских акций (по одному в строке).



2\. \*\*Асинхронная функция-генератор:\*\*



&nbsp;  \* Реализуйте `async`-функцию-генератор, которая построчно читает `tickers.txt` и выдаёт тикеры.



3\. \*\*Клиент для ISS API Московской биржи:\*\*



&nbsp;  \* Научитесь делать запросы к:



&nbsp;    \* `…/securities/{ticker}/dividends.json` — дивиденды;

&nbsp;    \* `…/history/…/{ticker}.json` — история котировок (цены закрытия);

&nbsp;    \* `…/{ticker}/dates.json` — границы доступных дат.

&nbsp;  \* Сначала можно сделать \*\*синхронную версию\*\* на `requests`, чтобы убедиться, что вы понимаете структуру ответа.

&nbsp;  \* Финальная версия должна использовать \*\*асинхронный клиент\*\* (`aiohttp` или аналогичный).



4\. \*\*Парсинг данных:\*\*



&nbsp;  \* Из ответа по дивидендам извлеките:



&nbsp;    \* дату выплаты,

&nbsp;    \* сумму дивиденда на одну акцию,

&nbsp;    \* валюту.

&nbsp;  \* Из ответа по истории котировок извлеките:



&nbsp;    \* дату торгов (`TRADEDATE`),

&nbsp;    \* цену закрытия (`CLOSE`).



5\. \*\*Работа с ограничением по 100 записей:\*\*



&nbsp;  \* Продумайте и реализуйте способ получить \*\*всю доступную историю котировок\*\*, несмотря на ограничение в 100 записей на ответ (потребуется пагинация или разбиение по датам).



6\. \*\*Сохранение в CSV:\*\*



&nbsp;  \* Для каждого тикера создайте \*\*два CSV-файла\*\*:



&nbsp;    \* `TICKER\_prices.csv` — даты и цены закрытия;

&nbsp;    \* `TICKER\_dividends.csv` — даты и величины дивидендов.

&nbsp;  \* Структуру файлов (имена столбцов, формат даты) выберите сами, но сделайте её разумной и однозначной.



7\. \*\*Требование к финальному решению:\*\*



&nbsp;  \* Общее решение (обработка всех тикеров из файла) должно использовать \*\*асинхронный подход\*\* для HTTP-запросов.

&nbsp;  \* По желанию: организуйте запись файлов через \*\*пул потоков\*\*, чтобы не блокировать event loop.



---



\## 10. Что сдавать



\* Python-скрипт(ы) с реализацией:



&nbsp; \* асинхронного чтения тикеров;

&nbsp; \* асинхронных запросов к ISS API;

&nbsp; \* парсинга и сохранения данных в CSV.

\* Текстовый файл с тикерами `tickers.txt`.

\* (Опционально) Краткое текстовое описание вашей архитектуры:



&nbsp; \* как организованы функции;

&nbsp; \* как вы решаете задачу получения всей истории котировок;

&nbsp; \* как обрабатываете ошибки (например, если тикер не найден).



Не бойтесь выкладывать код и обсуждать чужие решения.

Код-ревью — важная часть обучения.



В следующей части проекта на основе сохранённых CSV-файлов вы будете моделировать стратегии инвестирования и строить наглядные графики.



```




