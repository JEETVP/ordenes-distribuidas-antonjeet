from sqlalchemy import select
from models import Order

class OrdersRepository:

    def __init__(self, session):
        self.session = session #conexion con la base de datos

    def exists(self, order_id): #verifica que no haya otro objeto con el mismo id

        return self.session.query(Order)\
            .filter(Order.order_id == order_id)\
            .first() is not None

    def insert(self, order):

        db_order = Order(
            order_id=order.order_id,
            customer=order.customer,
            items=[item.dict() for item in order.items]
        )

        self.session.add(db_order) #se añade el objeto db_order a la base de datos
        self.session.commit() #guarda el cambio