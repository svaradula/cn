import asyncio

async def fetch_user(user_id: int) -> dict:
    print(f"Fetching user with id {user_id}...")
    await asyncio.sleep(3)  # simulating I/O
    return {"id": user_id, "name": "Manava"}

async def main():
    user = await fetch_user(10)
    print(user)

# def main():
#     user = asyncio.run(fetch_user(10))
#     print(user)

asyncio.run(main())
