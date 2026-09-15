import asyncio
import websockets
import json
import os
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Gold Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

API_TOKEN = os.environ.get("DERIV_TOKEN", "")
APP_ID = "1089"
TARGET_SYMBOL = "frxXAUUSD" # Deriv API symbol for Gold

async def run_bot():
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    traded = False

    while True:
        try:
            if not API_TOKEN:
                print("ERROR: DERIV_TOKEN is missing on Render environment!")
                await asyncio.sleep(10)
                continue

            print("Connecting to Deriv for Gold (XAUUSD)...")
            async with websockets.connect(ws_url) as ws:
                # Authorize session
                await ws.send(json.dumps({"authorize": API_TOKEN, "req_id": 1}))
                auth_res = await ws.recv()
                auth_data = json.loads(auth_res)

                if "error" in auth_data:
                    print(f"AUTH FAILED: {auth_data['error']['message']}")
                    await asyncio.sleep(10)
                    continue

                print("Authorized! Subscribing to Gold ticks...")
                await ws.send(json.dumps({"ticks": TARGET_SYMBOL, "req_id": 2}))
                
                async for message in ws:
                    data = json.loads(message)
                    msg_type = data.get("msg_type")
                    
                    if msg_type == "tick":
                        price = data.get("tick", {}).get("quote")
                        print(f"-> Gold Price: {price}")
                        
                        # Place a standard Call (Rise) option contract on Gold (No Multipliers)
                        if not traded:
                            traded = True
                            chosen_stake = 1
                            print(f"Sending Gold Rise contract proposal (Stake: ${chosen_stake})...")
                            
                            proposal_payload = {
                                "proposal": 1,
                                "amount": chosen_stake,
                                "basis": "stake",
                                "contract_type": "CALL", # Standard Rise option
                                "currency": "USD",
                                "symbol": TARGET_SYMBOL,
                                "duration": 5,
                                "duration_unit": "t", # 5 ticks duration
                                "req_id": 3
                            }
                            await ws.send(json.dumps(proposal_payload))
                            
                    elif msg_type == "proposal":
                        if "proposal" in data and "error" not in data:
                            proposal_id = data["proposal"]["id"]
                            ask_price = data["proposal"]["ask_price"]
                            print(f"Proposal received! Buying Gold contract at price {ask_price}...")
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
                            print(f"SUCCESS! Gold contract opened! ID: {contract_id}")

        except Exception as e:
            print(f"Connection error: {e}")
            await asyncio.sleep(5)

async def main():
    await run_bot()

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    asyncio.run(main())
