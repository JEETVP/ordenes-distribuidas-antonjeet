from models import Order


class OrdersRepository:
    def __init__(self, session):
        self.session = session  # conexion con la base de datos

    def exists(self, order_id):  # verifica que no haya otro objeto con el mismo id
        return (
            self.session.query(Order).filter(Order.order_id == order_id).first()
            is not None
        )

    def insert(self, order, claims):
        db_order = Order(
            order_id=order.order_id,
            customer=order.customer,
            items=[item.dict() for item in order.items],
            created_by_user_id=str(claims["sub"]),
            created_by_email=claims["email"],
        )

        self.session.add(db_order)
        self.session.commit()

    def list_for_user(self, claims):
        query = self.session.query(Order).order_by(Order.created_at.desc())

        if claims.get("role") != "admin":
            query = query.filter(Order.created_by_user_id == str(claims["sub"]))

        return query.all()
