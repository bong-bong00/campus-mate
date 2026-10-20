"""웹 화면은 메인 서버만 호출한다."""
import httpx

from config import MAIN_SERVER_URL


async def get(path: str, **params):
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.get(MAIN_SERVER_URL + path, params={k: v for k, v in params.items() if v})
        res.raise_for_status()
        return res.json()


async def post(path: str, data: dict):
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(MAIN_SERVER_URL + path, json=data)
        res.raise_for_status()
        return res.json()


async def delete(path: str):
    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.delete(MAIN_SERVER_URL + path)
        res.raise_for_status()
        return res.json()
