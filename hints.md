# Подсказки и рекомендации  
## Hints для выполнения части 1

Эти советы помогут вам выполнить задание корректно и эффективно, но не являются готовым решением.

---

## 1. Работа с API через браузер

Перед тем как писать код, откройте в браузере:

- Дивиденды:
  ```
  http://iss.moex.com/iss/securities/GMKN/dividends.json
  ```

- История цен:
  ```
  http://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/GMKN.json?from=2023-05-25&till=2023-05-27
  ```

- Границы дат:
  ```
  http://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/GMKN/dates.json
  ```

Посмотрите структуру JSON вручную.

---

## 2. Структура JSON в ответах

Обратите внимание:

- В каждом ответе есть блок:
  ```json
  {
    "columns": [...],
    "data": [...]
  }
  ```
- Вам нужно находить индексы нужных столбцов:
  ```python
  idx = columns.index("CLOSE")
  ```

---

## 3. Как получить более 100 записей истории котировок

ISS API позволяет использовать параметры:

- `start` — смещение (offset)
- `from` / `till` — фильтр по датам

Самые популярные способы:

### Способ 1 — использовать параметр `start`
Например:
```
?start=0
?start=100
?start=200
...
```

### Способ 2 — запрашивать небольшие диапазоны дат
Например:
- сначала 2000–2005,
- потом 2005–2010,
- и так далее.

Оба подхода допустимы.

---

## 4. Асинхронный HTTP-клиент aiohttp

Шаблон функции:

```python
async def fetch_json(session, url, params=None):
    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()
```

Создание сессии:

```python
async with aiohttp.ClientSession() as session:
    data = await fetch_json(session, url)
```

---

## 5. Асинхронный генератор тикеров

Вам нужно реализовать:

```python
async def ticker_generator(path):
    for line in open(path):
        await asyncio.sleep(0)
        yield line.strip()
```

Можно использовать `aiofiles`, но это не обязательно.

---

## 6. Как безопасно сохранять CSV

Чтобы не блокировать event loop:

- используйте `ThreadPoolExecutor`:

```python
loop = asyncio.get_running_loop()
await loop.run_in_executor(None, write_csv_func, data)
```

---

## 7. Автоматизация обработки нескольких тикеров

Для одновременного получения данных:

```python
tasks = [process_one_ticker(ticker) for ticker in tickers]
await asyncio.gather(*tasks)
```

---

## 8. Отладка

Советы:

- сначала напишите и протестируйте синхронную версию (`requests`);
- убедитесь, что правильно понимаете структуру JSON;
- проверьте один тикер вручную;
- только потом переходите к асинхронной реализации.

---

## 9. Типичные ошибки

- ❌ забыли обработать параметр `start` и получили только первые 100 записей;  
- ❌ неверно выбрали индексы колонок;  
- ❌ забыли `.raise_for_status()` — ошибки API остались незамеченными;  
- ❌ блокировали event loop синхронной записью в файл;  
- ❌ не обрабатывали пустые ответы API.

---

Удачи в выполнении! 