import asyncio
from solana.rpc.websocket_api import *
import os
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solders.signature import Signature
from solana.rpc.async_api import AsyncClient
from fetch_transaction import parse_trade
import re

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

        MIN_RAW_AMOUNT = 50000000
        is_high_value = False

        for log in logs:
            if "Swap" in log: 
                is_swap = True
                match = re.search(r"amount_in: (\d+)", log)

                if match:
                    raw_amount = int(match.group(1))
                    if raw_amount > MIN_RAW_AMOUNT:
                        is_high_value = True
        
        if is_swap and is_high_value:
            print("!", end="", flush=True) 
            
            return str(log_response.result.value.signature)
        return None

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
                    
                    if tx_info:
                        SOL_MINT = "So11111111111111111111111111111111111111112"
                        MIN_SOL_THRESHOLD = 0.2
                        
                        sol_amount = 0
                        is_whale = False
                        
                        if tx_info['bought_mint'] == SOL_MINT:
                            sol_amount = tx_info['bought_amount']
                            
                        elif tx_info['sold_mint'] == SOL_MINT:
                            sol_amount = tx_info['sold_amount']

                        if sol_amount >= MIN_SOL_THRESHOLD:
                            is_whale = True
                        
                        if is_whale:
                            print(f"🐋 {tx_info['signer']} | Swapped {tx_info['sold_amount']:.2f} {tx_info['sold_mint']} -> {tx_info['bought_amount']:.2f} {tx_info['bought_mint']}")
                        else:
                            print(f"Small swap: {sol_amount:.4f} SOL", end="", flush = True)

        except Exception as e:
            pass

if __name__ == "__main__":
    asyncio.run(main())
