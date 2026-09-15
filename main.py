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
    return "Divine Gold Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

APP_ID = "1089"
TARGET_SYMBOL = "R_75" 

async def trading_worker():
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    active_contracts = {}

    while True:
        try:
            print(f"Connecting to Deriv Public Feed for {TARGET_SYMBOL}...")
            async with websockets.connect(ws_url) as ws:
                print("Subscribing directly to market ticks...")
                await ws.send(json.dumps({"ticks": TARGET_SYMBOL, "req_id": 1}))
                
                async for message in ws:
                    data = json.loads(message)
                    msg_type = data.get("msg_type")
                    
                    if msg_type == "tick":
                        tick_data = data.get("tick", {})
                        price = tick_data.get("quote")
                        
                        if price:
                            print(f"Live Price [{TARGET_SYMBOL}]: {price} | Evaluating trade...")
                            
                            # 50% chance trigger with max 3 concurrent positions
                            if random.random() < 0.5 and len(active_contracts) < 3:
                                proposal_request = {
                                    "proposal": 1,
                                    "amount": 1,
                                    "basis": "stake",
                                    "contract_type": "MULTUP",
                                    "currency": "USD",
                                    "symbol": TARGET_SYMBOL,
                                    "multiplier": 20,
                                    "req_id": random.randint(100, 999)
                                }
                                await ws.send(json.dumps(proposal_request))
                                await asyncio.sleep(5)
                            
                    elif msg_type == "proposal":
                        if "proposal" in data and "error" not in data:
                            proposal_id = data["proposal"]["id"]
                            ask_price = data["proposal"]["ask_price"]
                            print(f"Proposal received (Cost: {ask_price}). Buying contract...")
                            buy_request = {
                                "buy": proposal_id,
                                "price": float(ask_price),
                                "req_id": random.randint(1000, 9999)
                            }
                            await ws.send(json.dumps(buy_request))
                        elif "error" in data:
                            print(f"Proposal Error: {data['error']['message']}")
                            
                    elif msg_type == "buy":
                        if "buy" in data:
                            contract_id = data["buy"]["contract_id"]
                            active_contracts[contract_id] = True
                            print(f"SUCCESS! Position live! Contract ID: {contract_id}")

        except Exception as e:
            print(f"Connection Exception: {e}")
            await asyncio.sleep(5)

async def main():
    await trading_worker()

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    asyncio.run(main())
