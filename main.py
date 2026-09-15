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
    return "Divine Gold Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# The bot pulls your token securely from Render environment variables
API_TOKEN = os.environ.get("DERIV_TOKEN", "")
APP_ID = "1089"
TARGET_SYMBOL = "R_75" 

async def run_bot():
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    traded = False

    while True:
        try:
            if not API_TOKEN:
                print("ERROR: DERIV_TOKEN is missing on Render environment! Please add it.")
                await asyncio.sleep(10)
                continue

            print("Connecting to Deriv WebSocket and authorizing...")
            async with websockets.connect(ws_url) as ws:
                # Authorize first (Required for multipliers)
                await ws.send(json.dumps({"authorize": API_TOKEN, "req_id": 1}))
                auth_res = await ws.recv()
                auth_data = json.loads(auth_res)

                if "error" in auth_data:
                    print(f"AUTH FAILED: {auth_data['error']['message']}")
                    await asyncio.sleep(10)
                    continue

                print("Authorized successfully! Subscribing to ticks...")
                await ws.send(json.dumps({"ticks": TARGET_SYMBOL, "req_id": 2}))
                
                async for message in ws:
                    data = json.loads(message)
                    msg_type = data.get("msg_type")
                    
                    if msg_type == "tick":
                        price = data.get("tick", {}).get("quote")
                        print(f"-> Live Price [{TARGET_SYMBOL}]: {price}")
                        
                        # Bot automatically chooses its own stake/lot size
                        if not traded:
                            traded = True
                            chosen_stake = random.choice([1, 2]) # Bot picks stake automatically
                            print(f"Bot choosing stake size: ${chosen_stake}. Sending trade proposal...")
                            
                            proposal_payload = {
                                "proposal": 1,
                                "amount": chosen_stake,
                                "basis": "stake",
                                "contract_type": "MULTUP",
                                "currency": "USD",
                                "symbol": TARGET_SYMBOL,
                                "multiplier": 20,
                                "limit_order": {
                                    "stop_loss": 0.50,
                                    "take_profit": 0.80
                                },
                                "req_id": 3
                            }
                            await ws.send(json.dumps(proposal_payload))
                            
                    elif msg_type == "proposal":
                        if "proposal" in data and "error" not in data:
                            proposal_id = data["proposal"]["id"]
                            ask_price = data["proposal"]["ask_price"]
                            print(f"Proposal received! Buying contract at price {ask_price}...")
                            buy_payload = {
                                "buy": proposal_id,
                                "price": float(ask_price),
                                "req_id": 4
                            }
                            await ws.send(json.dumps(buy_payload))
                        else:
                            print(f"Proposal error: {data.get('error', {}).get('message')}")
                            
                    elif msg_type == "buy":
                        if "buy" in data:
                            contract_id = data["buy"]["contract_id"]
                            print(f"SUCCESS! Trade opened successfully! ID: {contract_id}")

        except Exception as e:
            print(f"Connection error: {e}")
            await asyncio.sleep(5)

async def main():
    await run_bot()

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    asyncio.run(main())
