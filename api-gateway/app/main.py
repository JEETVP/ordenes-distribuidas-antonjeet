import uuid
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from auth import get_current_claims
from redis_client import redis_client
from schemas import OrderCreate
from services.auth_client import proxy_auth_request
from services.writer_client import fetch_orders_from_writer, send_order_to_writer

app = FastAPI(title="API Gateway")


@app.get("/health")
def health():
    return {"service": "api-gateway", "status": "ok"}


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(request: Request):
    response_status, payload = await proxy_auth_request("/auth/register", request)
    return JSONResponse(content=payload, status_code=response_status)


@app.post("/auth/login")
async def login(request: Request):
    response_status, payload = await proxy_auth_request("/auth/login", request)
    return JSONResponse(content=payload, status_code=response_status)


@app.get("/auth/me")
async def me(request: Request):
    response_status, payload = await proxy_auth_request("/auth/me", request)
    return JSONResponse(content=payload, status_code=response_status)


@app.get("/auth/verify")
async def verify(request: Request):
    response_status, payload = await proxy_auth_request("/auth/verify", request)
    return JSONResponse(content=payload, status_code=response_status)


@app.post("/auth/logout")
async def logout(request: Request):
    response_status, payload = await proxy_auth_request("/auth/logout", request)
    return JSONResponse(content=payload, status_code=response_status)


@app.post("/orders")
async def create_order(
    order: OrderCreate,
    request: Request,
    claims: dict = Depends(get_current_claims),
):
    order_id = str(uuid.uuid4())
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))

    redis_key = f"order:{order_id}"
    redis_client.hset(
        redis_key,
        mapping={
            "status": "RECEIVED",
            "last_update": datetime.utcnow().isoformat(),
            "created_by_user_id": claims["sub"],
            "created_by_email": claims["email"],
        },
    )

    payload = {
        "order_id": order_id,
        "customer": order.customer,
        "items": [item.model_dump() for item in order.items],
    }

    success = await send_order_to_writer(
        payload,
        request_id,
        request.headers.get("Authorization"),
    )

    if not success:
        redis_client.hset(
            redis_key,
            mapping={
                "status": "FAILED",
                "last_update": datetime.utcnow().isoformat(),
            },
        )
        raise HTTPException(status_code=502, detail="Writer service unavailable")

    return {
        "order_id": order_id,
        "status": "RECEIVED",
        "customer": order.customer,
        "requested_by": claims["email"],
    }


@app.get("/orders")
async def list_orders(
    request: Request,
    claims: dict = Depends(get_current_claims),
):
    try:
        orders = await fetch_orders_from_writer(request.headers.get("Authorization"))
    except Exception as error:
        raise HTTPException(status_code=502, detail="Writer service unavailable") from error

    for order in orders:
        redis_data = redis_client.hgetall(f"order:{order['order_id']}")
        order["status"] = redis_data.get("status", "UNKNOWN")
        order["last_update"] = redis_data.get("last_update")

    return orders


@app.get("/orders/{order_id}")
def get_order(order_id: str, claims: dict = Depends(get_current_claims)):
    redis_key = f"order:{order_id}"
    data = redis_client.hgetall(redis_key)

    if not data:
        raise HTTPException(status_code=404, detail="Order not found")

    if claims.get("role") != "admin" and data.get("created_by_user_id") != str(claims["sub"]):
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order_id,
        "status": data.get("status"),
        "last_update": data.get("last_update"),
        "created_by_email": data.get("created_by_email"),
        "requested_by": claims["email"],
    }
