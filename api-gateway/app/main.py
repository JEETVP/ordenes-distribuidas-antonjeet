from fastapi import FastAPI, HTTPException, Request
import uuid
from datetime import datetime

from redis_client import redis_client
from schemas import OrderCreate
from services.writer_client import send_order_to_writer

app = FastAPI(title="API Gateway")


@app.get("/")
def root():
    return {"service": "api-gateway"}


@app.post("/orders")
async def create_order(order: OrderCreate, request: Request):

    order_id = str(uuid.uuid4())
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))

    redis_key = f"order:{order_id}"

    redis_client.hset(
        redis_key,
        mapping={
            "status": "RECEIVED",
            "last_update": datetime.utcnow().isoformat()
        }
    )

    payload = {
        "order_id": order_id,
        "customer": order.customer,
        "items": [item.dict() for item in order.items]
    }

    success = await send_order_to_writer(payload, request_id)

    if not success:
        redis_client.hset(
            redis_key,
            mapping={
                "status": "FAILED",
                "last_update": datetime.utcnow().isoformat()
            }
        )

    return {
        "order_id": order_id,
        "status": "RECEIVED"
    }


@app.get("/orders/{order_id}")
def get_order(order_id: str):

    redis_key = f"order:{order_id}"

    data = redis_client.hgetall(redis_key)

    if not data:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order_id,
        "status": data.get("status"),
        "last_update": data.get("last_update")
    }