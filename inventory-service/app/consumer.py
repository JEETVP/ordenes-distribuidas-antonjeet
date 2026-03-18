import json
import threading
import time

import pika

from config import INVENTORY_QUEUE, ORDERS_EXCHANGE, RABBITMQ_URL
from db import SessionLocal
from repositories.inventory_repo import InventoryRepository


def _procesar_mensaje(ch, method, properties, body):
    mensaje = json.loads(body)
    items = mensaje.get("items", [])

    db = SessionLocal()

    try:
        repo = InventoryRepository(db)

        # recorro todos los productos de la orden para ir bajando stock
        for item in items:
            repo.reserve_stock(item["sku"], item["qty"])

        db.commit()

        print(
            f"inventory-service desconto stock de la orden {mensaje.get('order_id')}"
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as error:
        db.rollback()
        print(f"inventory-service fallo con la orden {mensaje.get('order_id')}: {error}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        db.close()


def _consumir():
    parametros = pika.URLParameters(RABBITMQ_URL)

    while True:
        try:
            conexion = pika.BlockingConnection(parametros)
            canal = conexion.channel()
            # si la cola no existe rabbit la crea y la deja lista
            canal.exchange_declare(exchange=ORDERS_EXCHANGE, exchange_type="fanout", durable=True)
            canal.queue_declare(queue=INVENTORY_QUEUE, durable=True)
            canal.queue_bind(exchange=ORDERS_EXCHANGE, queue=INVENTORY_QUEUE)
            canal.basic_qos(prefetch_count=1)
            canal.basic_consume(queue=INVENTORY_QUEUE, on_message_callback=_procesar_mensaje)
            canal.start_consuming()
        except Exception as error:
            print(f"inventory-service reconectando consumidor: {error}")
            time.sleep(3)


def iniciar_hilo_consumidor():
    # fastapi levanta la api y el consumidor se queda corriendo aparte
    hilo = threading.Thread(target=_consumir, daemon=True)
    hilo.start()
