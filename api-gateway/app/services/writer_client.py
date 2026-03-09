import httpx
from config import WRITER_SERVICE_URL, WRITER_TIMEOUT_SECONDS, WRITER_MAX_RETRIES

#aqui se hace una petición asincrona para mandar la orden del gateway al writer-service con http
async def send_order_to_writer(order_payload: dict, request_id: str):

    url = f"{WRITER_SERVICE_URL}/internal/orders" #url interna para la red de docker

    headers = {
        "X-Request-Id": request_id
    }

    for attempt in range(WRITER_MAX_RETRIES + 1):

        try:
            async with httpx.AsyncClient(timeout=WRITER_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    url,
                    json=order_payload,
                    headers=headers
                )

            if response.status_code in (200, 201): #caso de exito para el cliente http
                return True

        except Exception: #no se logra enviar
            if attempt == WRITER_MAX_RETRIES:
                return False

    return False