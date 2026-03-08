from sqlalchemy import select
from models import Order


class OrdersRepository:

    def __init__(self, session):
        self.session = session

    async def exists(self, order_id: str):

        query = select(Order).where(Order.order_id == order_id)

        result = await self.session.execute(query)

        return result.scalar_one_or_none() is not None

    async def insert(self, order):

        db_order = Order(
            order_id=order.order_id,
            customer=order.customer,
            items=[item.dict() for item in order.items]
        )

        self.session.add(db_order)

        await self.session.commit()