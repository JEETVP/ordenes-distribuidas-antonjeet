import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")

ORDERS_EXCHANGE = os.getenv("ORDERS_EXCHANGE", "orders")

NOTIFICATION_QUEUE = os.getenv("NOTIFICATION_QUEUE", "notification.order.created")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://notifications_user:notifications_pass@postgres-notifications:5432/notifications_db",
)
