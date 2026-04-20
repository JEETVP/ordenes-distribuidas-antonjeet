import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://orders_user:orders_pass@postgres:5432/orders_db",
)

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
