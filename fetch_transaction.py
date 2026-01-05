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
        print(parse_trade(tx))

def make_map(token_list, signer):
    balance = {}
    for item in token_list:
        if str(item.owner) == str(signer):
            balance[item.mint] = item.ui_token_amount.ui_amount or 0
    return balance

def parse_trade(tx_response):
    main_data = tx_response.value.transaction
    
    signer = main_data.transaction.message.account_keys[0]

    pre_snapshot = make_map(main_data.meta.pre_token_balances, signer)
    post_snapshot = make_map(main_data.meta.post_token_balances, signer)
    all_mints = set(pre_snapshot.keys()) | set(post_snapshot.keys())

    sold_mint = None
    sold_amount = 0
    bought_mint = None
    bought_amount = 0

    for mint in all_mints:
        pre_val = pre_snapshot.get(mint, 0)
        post_val = post_snapshot.get(mint, 0)
        delta = post_val - pre_val
        
        if delta == 0: continue
            
        if delta > 0:
            bought_mint = mint
            bought_amount = delta
        elif delta < 0:
            sold_mint = mint
            sold_amount = abs(delta)

    SOL_MINT = "So11111111111111111111111111111111111111112"
    
    if sold_mint is None:
        pre_sol = main_data.meta.pre_balances[0]
        post_sol = main_data.meta.post_balances[0]
        
        sol_change = (post_sol - pre_sol) / 10**9 

        if sol_change < 0:
            sold_mint = SOL_MINT
            sold_amount = abs(sol_change)

    if bought_mint is None:
        pre_sol = main_data.meta.pre_balances[0]
        post_sol = main_data.meta.post_balances[0]
        sol_change = (post_sol - pre_sol) / 10**9
        
        if sol_change > 0:
            bought_mint = SOL_MINT
            bought_amount = sol_change

    return {
        "signer": str(signer),
        "bought_mint": str(bought_mint),
        "bought_amount": bought_amount,
        "sold_mint": str(sold_mint),
        "sold_amount": sold_amount
    }

if __name__ == "__main__":
    tx_sig = "2XJwGuQbqrxPQoPSNjhEnp7wUAToSNHCqMgm71JshGyJwYSWjLhZjuLXi8bQmWicQ37JGuSrMHHqE5CnSPAK74gJ" 
    asyncio.run(fetch(tx_sig))
