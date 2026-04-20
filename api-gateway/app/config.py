import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8003")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

WRITER_SERVICE_URL = os.getenv(
    "WRITER_SERVICE_URL",
    "http://writer-service:8001" #es la ruta por la que puede comunicarse con el contenedor de writerservice
)

WRITER_TIMEOUT_SECONDS = float(
    os.getenv("WRITER_TIMEOUT_SECONDS", "1.0")
)

WRITER_MAX_RETRIES = int(
    os.getenv("WRITER_MAX_RETRIES", "1")
)
