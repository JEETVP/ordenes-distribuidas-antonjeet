from fastapi import Depends, FastAPI, HTTPException

from auth import get_current_claims
from consumer import iniciar_hilo_consumidor
from db import SessionLocal, engine
from models import Base
from repositories.inventory_repo import InventoryRepository
from schemas import InventorySeed

app = FastAPI(title="Inventory Service")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    iniciar_hilo_consumidor()


@app.get("/health")
def health():
    return {"service": "inventory-service", "status": "ok"}


@app.post("/inventory/seed")
def seed_inventory(payload: InventorySeed, claims: dict = Depends(get_current_claims)):
    db = SessionLocal()

    try:
        repo = InventoryRepository(db)
        item = repo.upsert_stock(payload.sku, payload.stock)
        db.commit()
        db.refresh(item)
        return {
            "sku": item.sku,
            "stock": item.stock,
            "updated_by": claims["email"],
        }
    finally:
        db.close()


@app.get("/inventory/{sku}")
def get_inventory(sku: str, claims: dict = Depends(get_current_claims)):
    db = SessionLocal()

    try:
        repo = InventoryRepository(db)
        item = repo.get(sku)

        if item is None:
            raise HTTPException(status_code=404, detail="SKU not found")

        return {
            "sku": item.sku,
            "stock": item.stock,
            "requested_by": claims["email"],
        }
    finally:
        db.close()
