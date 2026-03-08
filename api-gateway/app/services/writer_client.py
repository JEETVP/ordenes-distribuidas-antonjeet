import httpx
from config import WRITER_SERVICE_URL, WRITER_TIMEOUT_SECONDS, WRITER_MAX_RETRIES


async def send_order_to_writer(order_payload: dict, request_id: str):

    url = f"{WRITER_SERVICE_URL}/internal/orders"

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

            if response.status_code in (200, 201):
                return True

        except Exception:
            if attempt == WRITER_MAX_RETRIES:
                return False

    return False