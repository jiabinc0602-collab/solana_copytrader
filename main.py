from solana.rpc.async_api import AsyncClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

rpc_endpoint = os.getenv('RPC_ENDPOINT')

async def main():
    async with AsyncClient(rpc_endpoint) as client:
        res = await client.get_slot()
        print(res)
        print(res.value)

asyncio.run(main())

