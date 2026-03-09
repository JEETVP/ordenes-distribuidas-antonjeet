import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://orders_user:orders_pass@postgres:5432/orders_db" #URL de la base de datos
)

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis:6379/0" #URL de redis
)