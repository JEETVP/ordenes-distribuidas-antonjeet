import json
import time

import pika

from config import NOTIFICATION_QUEUE, ORDERS_EXCHANGE, RABBITMQ_URL


def procesar_evento(ch, method, properties, body):
    mensaje = json.loads(body)
    # aqui solo simulamos la confirmacion con un print
    print(
        f"notification-service mando confirmacion de la orden {mensaje.get('order_id')} para {mensaje.get('customer')}"
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    parametros = pika.URLParameters(RABBITMQ_URL)

    while True:
        try:
            conexion = pika.BlockingConnection(parametros)
            canal = conexion.channel()
            # escucha el mismo evento que inventario pero hace otra accion
            canal.exchange_declare(exchange=ORDERS_EXCHANGE, exchange_type="fanout", durable=True)
            canal.queue_declare(queue=NOTIFICATION_QUEUE, durable=True)
            canal.queue_bind(exchange=ORDERS_EXCHANGE, queue=NOTIFICATION_QUEUE)
            canal.basic_consume(queue=NOTIFICATION_QUEUE, on_message_callback=procesar_evento)
            print("notification-service esperando eventos order.created")
            canal.start_consuming()
        except Exception as error:
            print(f"notification-service intentando reconectar: {error}")
            time.sleep(3)


if __name__ == "__main__":
    main()
