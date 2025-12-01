from pathlib import Path

# Путь к файлу с тикерами
TICKERS_FILE: Path = Path("tickers.txt")

# Директория для сохранения CSV-файлов
OUTPUT_DIR: Path = Path("data")

# Максимальное количество записей истории в одной "странице" (лимит API MOEX)
HISTORY_PAGE_SIZE: int = 100

# Максимальное количество одновременно обрабатываемых тикеров
MAX_CONCURRENT_REQUESTS: int = 5

# Количество потоков для записи файлов
MAX_WORKERS: int = 4

# User-Agent для HTTP-запросов (некоторые сервисы не любят пустой UA)
USER_AGENT: str = "AsyncMoexClient/1.0 (educational project)"

# Таймаут HTTP-сессии (секунды)
HTTP_TIMEOUT: int = 60
