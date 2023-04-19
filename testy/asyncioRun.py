import asyncio

async def vysledek():
    return 100

a = asyncio.run(vysledek())
print(a)