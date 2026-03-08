import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

WRITER_SERVICE_URL = os.getenv(
    "WRITER_SERVICE_URL",
    "http://writer-service:8001"
)

WRITER_TIMEOUT_SECONDS = float(
    os.getenv("WRITER_TIMEOUT_SECONDS", "1.0")
)

WRITER_MAX_RETRIES = int(
    os.getenv("WRITER_MAX_RETRIES", "1")
)