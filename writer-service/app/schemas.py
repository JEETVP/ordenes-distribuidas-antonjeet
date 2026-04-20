from pydantic import BaseModel
from typing import List


class Item(BaseModel):
    sku: str
    qty: int


class InternalOrder(BaseModel):
    order_id: str | None = None
    customer: str
    items: List[Item]


#unico cambio que tiene para recibir las ordenes del apigateway es que ya recibi un order id por que en este punto el flujo ya le asigno uno como tal
