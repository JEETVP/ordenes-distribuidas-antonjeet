import json
import time
import pika
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import NOTIFICATION_QUEUE, ORDERS_EXCHANGE, RABBITMQ_URL, DATABASE_URL
from models import Base, Notification

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(bind=engine)


def guardar_notificacion(data):
    session = SessionLocal()
    try:
        notif = Notification(
            order_id=data.get("order_id"),
            customer=data.get("customer"),
            event_type=data.get("event_type", "order.created"),
            message=f"Orden {data.get('order_id')} confirmada para {data.get('customer')}",
            reason=data.get("reason")
        )
        session.add(notif)
        session.commit()

        print(f"[DB] Notificación guardada: {notif.order_id}")

    except Exception as e:
        session.rollback()
        print(f"[DB ERROR] {e}")
        raise e

    finally:
        session.close()


def procesar_evento(ch, method, properties, body):
    try:
        mensaje = json.loads(body)

        print(f"[EVENTO] Recibido: {mensaje}")

        guardar_notificacion(mensaje)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[ERROR] procesando evento: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main():
    Base.metadata.create_all(bind=engine)

    parametros = pika.URLParameters(RABBITMQ_URL)

    while True:
        try:
            print("[INFO] Conectando a RabbitMQ...")

            conexion = pika.BlockingConnection(parametros)
            canal = conexion.channel()

            canal.exchange_declare(
                exchange=ORDERS_EXCHANGE,
                exchange_type="fanout",
                durable=True
            )

            canal.queue_declare(
                queue=NOTIFICATION_QUEUE,
                durable=True
            )

            canal.queue_bind(
                exchange=ORDERS_EXCHANGE,
                queue=NOTIFICATION_QUEUE
            )

            canal.basic_qos(prefetch_count=1)

            canal.basic_consume(
                queue=NOTIFICATION_QUEUE,
                on_message_callback=procesar_evento
            )

            print("[OK] notification-service esperando eventos...")

            canal.start_consuming()

        except Exception as error:
            print(f"[RECONNECT] Error: {error}")
            print("[RECONNECT] Reintentando en 3 segundos...")
            time.sleep(3)


if __name__ == "__main__":
    main()