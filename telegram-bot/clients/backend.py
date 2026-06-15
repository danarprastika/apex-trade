import os

import httpx


class BackendClient:
    def __init__(self):
        self.base_url = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1").rstrip("/")
        self.timeout = httpx.Timeout(10)

    async def get(self, path: str, token: str | None = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(path, headers=headers)
            response.raise_for_status()
            return response.json()

    async def post(self, path: str, payload: dict, token: str | None = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(path, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def delete(self, path: str, token: str | None = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.delete(path, headers=headers)
            response.raise_for_status()
            return response.json()
