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
    return "Divine Multi-Stream Matrix Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

API_TOKEN = "pat_9ea5fd57fa2cfc960e7c30d0f7a737d559dc6dc258dcf572d32bae26999092e8"
APP_ID = "1089"

SYMBOLS = ["R_75", "R_100", "1HZ100V", "R_50"]

async def trade_worker(symbol):
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    active_contracts = {}

    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                auth_payload = {"authorize": API_TOKEN, "req_id": random.randint(1, 1000)}
                await ws.send(json.dumps(auth_payload))
                await ws.recv()
                
                print(f"[{symbol}] Connected & Authorized. Ready for multi-queue execution...")
                await ws.send(json.dumps({"ticks": symbol, "req_id": random.randint(1001, 2000)}))
                
                async for message in ws:
                    data = json.loads(message)
                    msg_type = data.get("msg_type")
                    
                    if msg_type == "tick":
                        # Fire independent multi-market entry requests
                        if random.random() < 0.5 and len(active_contracts) < 3:
                            chosen_stake = random.choice([1, 2, 3])
                            chosen_multiplier = 50 if chosen_stake == 1 else 100
                            
                            print(f"[{symbol}] Firing simultaneous order! Stake: ${chosen_stake}")
                            
                            proposal_request = {
                                "proposal": 1,
                                "amount": chosen_stake,
                                "basis": "stake",
                                "contract_type": "MULTUP",
                                "currency": "USD",
                                "symbol": symbol,
                                "multiplier": chosen_multiplier,
                                "req_id": random.randint(2001, 5000),
                                "limit_order": {
                                    "stop_loss": round(chosen_stake * 0.5, 2),
                                    "take_profit": round(chosen_stake * 1.0, 2)
                                }
                            }
                            await ws.send(json.dumps(proposal_request))
                            await asyncio.sleep(6) # Faster cycling
                            
                    elif msg_type == "proposal":
                        if "proposal" in data:
                            proposal_id = data["proposal"]["id"]
                            payout = data["proposal"]["ask_price"]
                            buy_request = {
                                "buy": proposal_id,
                                "price": float(payout) + 2,
                                "req_id": random.randint(5001, 9999)
                            }
                            await ws.send(json.dumps(buy_request))
                            
                    elif msg_type == "buy":
                        if "buy" in data:
                            contract_id = data["buy"]["contract_id"]
                            active_contracts[contract_id] = True
                            print(f"[{symbol}] MULTI-TRADE SUCCESS! Active ID: {contract_id}")

        except Exception as e:
            print(f"[{symbol}] Reconnecting due to: {e}")
            await asyncio.sleep(5)

async def main():
    workers = [trade_worker(symbol) for symbol in SYMBOLS]
    await asyncio.gather(*workers)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    asyncio.run(main())
