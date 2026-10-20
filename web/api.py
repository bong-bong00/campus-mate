"""웹 화면은 메인 서버만 호출한다."""
import httpx

from config import MAIN_SERVER_URL


async def get(path: str, **params):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(MAIN_SERVER_URL + path,
                                    params={key: value for key, value in params.items() if value})
        response.raise_for_status()
        return response.json()


async def post(path: str, data: dict):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(MAIN_SERVER_URL + path, json=data)
        response.raise_for_status()
        return response.json()


async def delete(path: str):
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.delete(MAIN_SERVER_URL + path)
        response.raise_for_status()
        return response.json()
