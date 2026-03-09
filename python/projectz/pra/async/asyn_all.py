import asyncio

async def job(n):
    try:
        await asyncio.sleep(2)
        return f"done {n}"
    except Exception as e:
        print(f"Error in job {n}: {e}")
        return f"error {n}"

async def main():
    tasks = [asyncio.create_task(job(i)) for i in range(5)]
    results = await asyncio.gather(*tasks)
    print(results)

asyncio.run(main())
