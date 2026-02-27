import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Login
        resp_login = await client.post("/auth/login", json={
            "email": "test_new_user@example.com",
            "password": "password123"
        })
        print("Login:", resp_login.status_code, resp_login.text)
        
        # 2. Ingest
        resp_ingest = await client.post("/api/ingest/text", json={
            "text": "Hello world this is a test.",
            "title": "A title"
        })
        print("Ingest:", resp_ingest.status_code, resp_ingest.text)

asyncio.run(main())
