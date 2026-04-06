import json

import pika

from config import ORDERS_EXCHANGE, RABBITMQ_URL


def publicar_orden_creada(mensaje: dict) -> None:
    parametros = pika.URLParameters(RABBITMQ_URL)
    conexion = pika.BlockingConnection(parametros)

    try:
        canal = conexion.channel()
        canal.exchange_declare(exchange=ORDERS_EXCHANGE, exchange_type="topic", durable=True)
        canal.basic_publish(
            exchange=ORDERS_EXCHANGE,
            routing_key="order.created",  # necesario para topic
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
    finally:
        conexion.close()