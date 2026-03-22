import aiohttp
import logging
import asyncio

class HTTPClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.refresh_token = None
        self.session = None

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def login(self):
        await self._ensure_session()
        async with self.session.post(f"{self.base_url}/api/auth/token", json={
            "username": self.username,
            "password": self.password
        }) as resp:
            if resp.status == 200:
                data = await resp.json()
                self.token = data.get("access")
                self.refresh_token = data.get("refresh")
                return True
            return False

    async def post_telemetry(self, project_id, data):
        await self._ensure_session()
        headers = {"Authorization": f"Bearer {self.token}"}
        async with self.session.post(
            f"{self.base_url}/api/telemetry/evn/project/{project_id}",
            json=data,
            headers=headers
        ) as resp:
            if resp.status == 401: # Token expired
                if await self.login():
                    return await self.post_telemetry(project_id, data)
            return resp.status in [200, 201]

    async def close(self):
        if self.session:
            await self.session.close()
