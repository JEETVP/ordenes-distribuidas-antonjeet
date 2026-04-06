from fastapi import FastAPI
from datetime import datetime
import uuid
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
def create_order(order: InternalOrder):

    db = SessionLocal()
    repo = OrdersRepository(db)

    if not order.order_id:
        order.order_id = str(uuid.uuid4())

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

    redis_client.hset(
        f"order:{order.order_id}",
        mapping={"status": "PERSISTED"}
    )

    db.close()

    return {"order_id": order.order_id, "status": "PERSISTED"}