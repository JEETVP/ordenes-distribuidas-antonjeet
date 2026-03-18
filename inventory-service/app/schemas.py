from pydantic import BaseModel


class InventorySeed(BaseModel):
    sku: str
    stock: int
