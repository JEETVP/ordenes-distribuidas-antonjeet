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
async def create_order(order: OrderCreate, request: Request): #tiene que recibir el esquema de order create

    order_id = str(uuid.uuid4()) #identificador aleatorio como string
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))

    redis_key = f"order:{order_id}" #asigna una clava para que podamos consultar en redis

    redis_client.hset(
        redis_key,
        mapping={ #guarda en redis con un estado inicial de recibido, pasa a persisted cuando lo recive el writer-service
            "status": "RECEIVED",
            "last_update": datetime.utcnow().isoformat()
        }
    )

    payload = { # define lo que tiene que enviar al writer service
        "order_id": order_id,
        "customer": order.customer,
        "items": [item.dict() for item in order.items]
    }

    success = await send_order_to_writer(payload, request_id) #espera para mandar la orden al writer-service

    if not success:
        redis_client.hset(
            redis_key,
            mapping={
                "status": "FAILED",
                "last_update": datetime.utcnow().isoformat()
            }
        )

    return { #caso de exito e
        "order_id": order_id,
        "status": "RECEIVED"
    }


@app.get("/orders/{order_id}")
def get_order(order_id: str):

    redis_key = f"order:{order_id}" #busca con la clave de redis

    data = redis_client.hgetall(redis_key)

    if not data:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order_id,
        "status": data.get("status"),
        "last_update": data.get("last_update")
    }