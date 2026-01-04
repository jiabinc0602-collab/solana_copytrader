import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature
import os
from dotenv import load_dotenv

load_dotenv()

rpc_endpoint = os.getenv('RPC_ENDPOINT')

async def fetch(signature:str):
    async with AsyncClient(rpc_endpoint) as client:
        sig = Signature.from_string(signature)
        tx = await client.get_transaction(
            sig,
            max_supported_transaction_version=0
        )
        print(tx)

if __name__ == "__main__":
    tx_sig = "2XJwGuQbqrxPQoPSNjhEnp7wUAToSNHCqMgm71JshGyJwYSWjLhZjuLXi8bQmWicQ37JGuSrMHHqE5CnSPAK74gJ" 
    asyncio.run(fetch(tx_sig))