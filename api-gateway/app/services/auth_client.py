import json

import httpx
from fastapi import HTTPException, Request, status

from config import AUTH_SERVICE_URL


async def proxy_auth_request(path: str, request: Request) -> tuple[int, dict]:
    url = f"{AUTH_SERVICE_URL}{path}"
    json_body = None

    if request.method in {"POST", "PUT", "PATCH"}:
        body = await request.body()
        if body:
            try:
                json_body = json.loads(body)
            except json.JSONDecodeError as error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON payload",
                ) from error

    headers = {}

    authorization = request.headers.get("Authorization")
    if authorization:
        headers["Authorization"] = authorization

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.request(
                request.method,
                url,
                json=json_body,
                headers=headers,
            )
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Auth service unavailable",
        ) from error

    return response.status_code, response.json()
