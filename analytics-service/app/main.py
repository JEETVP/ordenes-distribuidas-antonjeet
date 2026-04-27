import json
import time

import pika
import redis

from config import ANALYTICS_QUEUE, ORDERS_EXCHANGE, RABBITMQ_URL, REDIS_URL

cliente_redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def procesar_evento(ch, method, properties, body):
    mensaje = json.loads(body)
    items = mensaje.get("items", [])
    # aqui saco cuantas piezas venian en la orden
    cantidad_total = sum(item.get("qty", 0) for item in items)

    # dejamos la metrica en redis para no meter otra base
    total_ordenes = cliente_redis.incr("metrica:ordenes_creadas")
    total_productos = cliente_redis.incrby("metrica:productos_pedidos", cantidad_total)

    print(
        f"analytics-service guardo metrica: ordenes={total_ordenes}, productos={total_productos}, order_id={mensaje.get('order_id')}"
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    parametros = pika.URLParameters(RABBITMQ_URL)

    while True:
        try:
            conexion = pika.BlockingConnection(parametros)
            canal = conexion.channel()
            # este exchange es el mismo que usa writer-service al publicar
            canal.exchange_declare(
                exchange=ORDERS_EXCHANGE, exchange_type="fanout", durable=True
            )
            canal.queue_declare(queue=ANALYTICS_QUEUE, durable=True)
            canal.queue_bind(exchange=ORDERS_EXCHANGE, queue=ANALYTICS_QUEUE)
            canal.basic_consume(
                queue=ANALYTICS_QUEUE, on_message_callback=procesar_evento
            )
            print("analytics-service esperando eventos order.created")
            canal.start_consuming()
        except Exception as error:
            print(f"analytics-service intentando reconectar: {error}")
            time.sleep(3)


if __name__ == "__main__":
    main()
