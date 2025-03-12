import httpx


async def fetch_data(url: str, params: dict = None):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
