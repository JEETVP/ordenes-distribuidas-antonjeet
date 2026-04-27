import uuid
from datetime import datetime

from fastapi import Depends, FastAPI
from sqlalchemy import text

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
    migrate_orders()


def migrate_orders():
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS created_by_user_id VARCHAR(50)"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS created_by_email VARCHAR(255)"
            )
        )
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_orders_created_by_user_id
                ON orders (created_by_user_id)
                """
            )
        )


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
            repo.insert(order, claims)
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


@app.get("/internal/orders")
def list_orders(claims: dict = Depends(get_current_claims)):
    db = SessionLocal()
    try:
        repo = OrdersRepository(db)
        orders = repo.list_for_user(claims)

        return [
            {
                "order_id": order.order_id,
                "customer": order.customer,
                "items": order.items or [],
                "created_by_user_id": order.created_by_user_id,
                "created_by_email": order.created_by_email,
                "created_at": order.created_at,
            }
            for order in orders
        ]
    finally:
        db.close()
