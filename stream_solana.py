import asyncio
from solana.rpc.websocket_api import *
import os
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solders.signature import Signature
from solana.rpc.async_api import AsyncClient
from fetch_transaction import parse_trade
import traceback
import random

load_dotenv()

raydium_id = Pubkey.from_string(os.getenv('RAYDIUM_AMM_ID'))
wss_endpoint = os.getenv('WSS_ENDPOINT')
rpc_endpoint = os.getenv('RPC_ENDPOINT')

request_semaphore = asyncio.Semaphore(10)

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

            print(".", end="", flush=True)

            for msg in next_resp:
                signature_str = process_transaction(msg)
                if signature_str:
                    asyncio.create_task(analyze_trade(signature=signature_str))

def process_transaction(log_response):
    try:
        if log_response.result.value.err is not None:
            return None
        
        logs = log_response.result.value.logs
        is_swap = False

        for log in logs:
            if "Swap" in log: 
                is_swap = True
                break
        
        if is_swap:
            print("!", end="", flush=True) 
            
            return str(log_response.result.value.signature)

    except Exception:
        return None

async def analyze_trade(signature):
    async with request_semaphore:
        try:
            async with AsyncClient(rpc_endpoint) as client:
                sig = Signature.from_string(signature)
                
                tx_resp = await client.get_transaction(
                    sig,
                    max_supported_transaction_version=0
                )
                
                if tx_resp.value:
                    tx_info = parse_trade(tx_response=tx_resp)
                    
                    if tx_info and tx_info['bought_amount'] > 0:
                        print(f"\n💸 {tx_info['signer']} | +{tx_info['bought_amount']:.4f} {tx_info['bought_mint']}")
                    else:
                        print("?", end="", flush=True)
    
        except Exception as e:
            pass

if __name__ == "__main__":
    asyncio.run(main())
