import asyncio
import websockets
import json
import random
import os
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Divine Advanced Multi-Market Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

API_TOKEN = "pat_9ea5fd57fa2cfc960e7c30d0f7a737d559dc6dc258dcf572d32bae26999092e8"
APP_ID = "1089"

SYMBOLS = ["frxXAUUSD", "frxEURUSD", "frxGBPUSD", "frxAUDUSD"]

async def trade_worker(symbol):
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    active_contracts = {} # Tracks open contract IDs and their entry quotes

    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                auth_payload = {"authorize": API_TOKEN}
                await ws.send(json.dumps(auth_payload))
                await ws.recv()
                
                print(f"[{symbol}] Connected & Authorized. Monitoring market...")
                await ws.send(json.dumps({"ticks": symbol}))
                
                async for message in ws:
                    data = json.loads(message)
                    msg_type = data.get("msg_type")
                    
                    if msg_type == "tick":
                        tick_data = data.get("tick", {})
                        current_price = tick_data.get("quote")
                        
                        # 1. Reversal Check for open positions: if price moves against us sharply, close early
                        for cid, entry_price in list(active_contracts.items()):
                            # Simple reversal detection logic (e.g. if price shifts significantly against entry)
                            if abs(current_price - entry_price) > (entry_price * 0.0015):
                                print(f"[{symbol}] Reversal detected! Closing contract {cid} early to protect capital.")
                                close_request = {"sell": cid, "price": 0}
                                await ws.send(json.dumps(close_request))
                                del active_contracts[cid]

                        # 2. Frequent entry trigger for multiple simultaneous positions
                        if random.random() < 0.4 and len(active_contracts) < 3:
                            chosen_stake = random.choice([1, 2, 3])
                            chosen_multiplier = 50 if chosen_stake == 1 else 100
                            
                            print(f"[{symbol}] Opening setup! Stake: ${chosen_stake} ({chosen_multiplier}x)")
                            
                            proposal_request = {
                                "proposal": 1,
                                "amount": chosen_stake,
                                "basis": "stake",
                                "contract_type": "MULTUP",
                                "currency": "USD",
                                "symbol": symbol,
                                "multiplier": chosen_multiplier,
                                "limit_order": {
                                    "stop_loss": round(chosen_stake * 0.5, 2),
                                    "take_profit": round(chosen_stake * 1.0, 2)
                                }
                            }
                            await ws.send(json.dumps(proposal_request))
                            await asyncio.sleep(8) # Shorter cooldown to allow multiple trades
                            
                    elif msg_type == "proposal":
                        if "proposal" in data:
                            proposal_id = data["proposal"]["id"]
                            payout = data["proposal"]["ask_price"]
                            buy_request = {
                                "buy": proposal_id,
                                "price": float(payout) + 2
                            }
                            await ws.send(json.dumps(buy_request))
                            
                    elif msg_type == "buy":
                        if "buy" in data:
                            contract_id = data["buy"]["contract_id"]
                            # Store contract with a baseline dummy price for reversal tracking
                            active_contracts[contract_id] = 1.1500 
                            print(f"[{symbol}] SUCCESS! Multi-position active! ID: {contract_id}")
                            
                    elif msg_type == "sell":
                        if "sell" in data:
                            print(f"[{symbol}] Position successfully closed early due to reversal signal.")

        except Exception as e:
            print(f"[{symbol}] Connection error: {e}. Reconnecting...")
            await asyncio.sleep(5)

async def main():
    workers = [trade_worker(symbol) for symbol in SYMBOLS]
    await asyncio.gather(*workers)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    asyncio.run(main())
