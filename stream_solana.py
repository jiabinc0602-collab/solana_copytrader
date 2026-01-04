import asyncio
from solana.rpc.websocket_api import *
import os
from dotenv import load_dotenv
from solders.pubkey import Pubkey

load_dotenv()

raydium_id = Pubkey.from_string(os.getenv('RAYDIUM_AMM_ID'))
wss_endpoint = os.getenv('WSS_ENDPOINT')

async def main():
    async with connect(wss_endpoint) as websocket:
        await websocket.logs_subscribe(
            filter_ = RpcTransactionLogsFilterMentions(raydium_id),
            commitment="processed"
        )
        first_resp = await websocket.recv()
        subscription_id = first_resp[0].result

        print(subscription_id)
        print("Listening for Raydium trades...")
        while True:
            next_resp = await websocket.recv()

            for msg in next_resp:
                transaction = process_transaction(msg)
                print(f"Swap detected: {transaction}!")

def process_transaction(log_response):
    if log_response.result.value.err is not None:
        return
    
    logs = log_response.result.value.logs

    is_swap = False

    for log in logs:
        if "SwapBaseIn" in log or "SwapBaseOut" in log:
            is_swap = True
            break
    

    if is_swap:
        return log_response.result.value.signature



asyncio.run(main())
