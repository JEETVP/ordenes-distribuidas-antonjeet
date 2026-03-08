from fastapi import FastAPI
from datetime import datetime

from db import AsyncSessionLocal
from schemas import InternalOrder
from repositories.orders_repo import OrdersRepository
from redis_client import redis_client

app = FastAPI(title="Writer Service")


@app.get("/")
def root():
    return {"service": "writer-service"}


@app.post("/internal/orders")
async def create_order(order: InternalOrder):

    async with AsyncSessionLocal() as session:

        repo = OrdersRepository(session)

        exists = await repo.exists(order.order_id)

        if not exists:
            await repo.insert(order)

        redis_client.hset(
            f"order:{order.order_id}",
            mapping={
                "status": "PERSISTED",
                "last_update": datetime.utcnow().isoformat()
            }
        )

        return {
            "order_id": order.order_id,
            "status": "PERSISTED"
        }