import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")

ORDERS_EXCHANGE = os.getenv("ORDERS_EXCHANGE", "orders")

ANALYTICS_QUEUE = os.getenv("ANALYTICS_QUEUE", "analytics.order.created")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
