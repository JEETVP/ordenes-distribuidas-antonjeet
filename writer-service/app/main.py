import uuid
from datetime import datetime

from fastapi import Depends, FastAPI

from auth import get_current_claims
from db import SessionLocal, engine
from models import Base
from repositories.orders_repo import OrdersRepository
from redis_client import redis_client
from schemas import InternalOrder
from services.events import publicar_orden_creada

app = FastAPI(title="Writer Service")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"service": "writer-service", "status": "ok"}


@app.post("/internal/orders")
def create_order(order: InternalOrder, claims: dict = Depends(get_current_claims)):
    db = SessionLocal()
    try:
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
                    "created_at": datetime.utcnow().isoformat(),
                    "requested_by": claims["email"],
                }
            )

        redis_client.hset(
            f"order:{order.order_id}",
            mapping={"status": "PERSISTED"},
        )

        return {
            "order_id": order.order_id,
            "status": "PERSISTED",
            "requested_by": claims["email"],
        }
    finally:
        db.close()
