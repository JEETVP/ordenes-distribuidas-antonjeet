from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    sku = Column(String(50), primary_key=True)
    stock = Column(Integer, nullable=False, default=0)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
