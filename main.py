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
    return "Divine Unauthenticated Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

APP_ID = "1089"
TARGET_SYMBOL = "R_75" 

async def public_market_worker():
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"

    while True:
        try:
            print(f"Connecting to Deriv Public Feed for {TARGET_SYMBOL}...")
            async with websockets.connect(ws_url) as ws:
                # Skip authorization entirely and subscribe straight to ticks
                print("Subscribing directly to market ticks...")
                await ws.send(json.dumps({"ticks": TARGET_SYMBOL, "req_id": 1}))
                
                async for message in ws:
                    data = json.loads(message)
                    msg_type = data.get("msg_type")
                    
                    if msg_type == "tick":
                        tick_data = data.get("tick", {})
                        price = tick_data.get("quote")
                        print(f"SUCCESS! Live Tick received for {TARGET_SYMBOL} -> Price: {price}")
                        
        except Exception as e:
            print(f"Connection Exception: {e}")
            await asyncio.sleep(5)

async def main():
    await public_market_worker()

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    asyncio.run(main())
