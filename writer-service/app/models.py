from sqlalchemy import Column, String, JSON, TIMESTAMP, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Order(Base):

    __tablename__ = "orders"

    order_id = Column(String(36), primary_key=True)
    customer = Column(String(255))
    items = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())

    #es lo que va a guardar la base de datos.