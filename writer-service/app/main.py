from fastapi import FastAPI
from datetime import datetime

from db import SessionLocal
from schemas import InternalOrder
from repositories.orders_repo import OrdersRepository
from redis_client import redis_client

app = FastAPI(title="Writer Service")


@app.get("/")
def root():
    return {"service": "writer-service"}


@app.post("/internal/orders")
def create_order(order: InternalOrder): #validacion con internal order de schemas.py

    db = SessionLocal() #sesion para la transaccion

    repo = OrdersRepository(db) #ejecuta las consultas para ver si existe la orden y hacer la insercion

    exists = repo.exists(order.order_id)

    if not exists:
        repo.insert(order)

    redis_client.hset( #modifica el estado en edis
        f"order:{order.order_id}",
        mapping={"status": "PERSISTED"}
    )

    db.close() #cierra la conexion y devuelve el cambio de estado como respuesta

    return {"order_id": order.order_id, "status": "PERSISTED"}