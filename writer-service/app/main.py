from fastapi import FastAPI
from datetime import datetime

from db import SessionLocal, engine
from models import Base
from schemas import InternalOrder
from repositories.orders_repo import OrdersRepository
from redis_client import redis_client
from services.events import publicar_orden_creada

app = FastAPI(title="Writer Service")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


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
        publicar_orden_creada(
            {
                "event": "order.created",
                "order_id": order.order_id,
                "customer": order.customer,
                "items": [item.model_dump() for item in order.items],
                "created_at": datetime.utcnow().isoformat()
            }
        )

    redis_client.hset( #modifica el estado en edis
        f"order:{order.order_id}",
        mapping={"status": "PERSISTED"}
    )

    db.close() #cierra la conexion y devuelve el cambio de estado como respuesta

    return {"order_id": order.order_id, "status": "PERSISTED"}
