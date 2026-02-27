import httpx
import asyncio
import json

async def test():
    print("Submitting C12345 application for GHS2024...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://127.0.0.1:8000/api/v1/apply",
                json={"citizen_id": "C12345", "scheme_id": "GHS2024"},
                timeout=30.0
            )
            print(f"Status Code: {resp.status_code}")
            print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
