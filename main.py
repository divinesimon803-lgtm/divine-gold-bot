import asyncio
import websockets
import json
import random
import os
from flask import Flask
import threading

# Keep-Alive Web Server for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Divine Async Multi-Market Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

API_TOKEN = "pat_9ea5fd57fa2cfc960e7c30d0f7a737d559dc6dc258dcf572d32bae26999092e8"
APP_ID = "1089"

# Target markets with Gold as the primary focus
SYMBOLS = ["frxXAUUSD", "frxEURUSD", "frxGBPUSD", "frxAUDUSD"]

async def trade_worker(symbol):
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    
    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                # Authorize
                auth_payload = {"authorize": API_TOKEN}
                await ws.send(json.dumps(auth_payload))
                auth_resp = await ws.recv()
                
                print(f"[{symbol}] Authorized successfully. Listening for entries...")
                
                # Subscribe to ticks
                await ws.send(json.dumps({"ticks": symbol}))
                
                async for message in ws:
                    data = json.loads(message)
                    msg_type = data.get("msg_type")
                    
                    if msg_type == "tick":
                        # Random trigger interval to space out multi-market entries
                        if random.random() < 0.3:
                            chosen_stake = random.choice([1, 2, 3])
                            chosen_multiplier = 50 if chosen_stake == 1 else 100
                            
                            print(f"[{symbol}] Setup found! Executing Stake: ${chosen_stake} ({chosen_multiplier}x)")
                            
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
                            await asyncio.sleep(20) # Cooldown per symbol
                            
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
                            print(f"[{symbol}] SUCCESS! Trade opened! ID: {contract_id}")
                            
        except Exception as e:
            print(f"[{symbol}] Connection dropped: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

async def main():
    # Run all symbol workers concurrently
    workers = [trade_worker(symbol) for symbol in SYMBOLS]
    await asyncio.gather(*workers)

if __name__ == "__main__":
    # Start web server thread
    t = threading.Thread(target=run_web)
    t.start()
    
    # Run async event loop for the trading workers
    asyncio.run(main())
