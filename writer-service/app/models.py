from sqlalchemy import Column, String, JSON, TIMESTAMP, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Order(Base):

    __tablename__ = "orders"

    order_id = Column(String(36), primary_key=True)
    customer = Column(String(255))
    items = Column(JSON)
    created_by_user_id = Column(String(50), nullable=True, index=True)
    created_by_email = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    #es lo que va a guardar la base de datosssssss.
