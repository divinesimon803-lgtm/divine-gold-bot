import websocket
import json
import threading
import time
import random
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Divine Multi-Market Matrix Bot is active!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

API_TOKEN = "pat_9ea5fd57fa2cfc960e7c30d0f7a737d559dc6dc258dcf572d32bae26999092e8"
APP_ID = "1089" 

SYMBOLS = ["frxXAUUSD", "frxEURUSD", "frxGBPUSD", "frxAUDUSD"]
last_trade_times = {symbol: 0 for symbol in SYMBOLS}

def on_open(ws):
    print("Connected to Deriv API successfully!")
    auth_data = {"authorize": API_TOKEN}
    ws.send(json.dumps(auth_data))

def on_message(ws, message):
    global last_trade_times
    data = json.loads(message)
    msg_type = data.get("msg_type")
    
    if msg_type == "authorize":
        print("Authorization Successful! Subscribing to multi-market feeds...")
        for symbol in SYMBOLS:
            ws.send(json.dumps({"ticks": symbol}))
            time.sleep(0.3)
            
    elif msg_type == "tick":
        tick_data = data.get("tick", {})
        symbol = tick_data.get("symbol")
        quote = tick_data.get("quote")
        
        current_time = time.time()
        # Check each symbol independently every 15 seconds for multi-market spread
        if symbol in last_trade_times and (current_time - last_trade_times[symbol] > 15):
            
            chosen_stake = random.choice([1, 2, 3])
            chosen_multiplier = 50 if chosen_stake == 1 else 100
            
            print(f"[{symbol}] Multi-market setup found! Placing Stake: ${chosen_stake} ({chosen_multiplier}x)")
            
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
            ws.send(json.dumps(proposal_request))
            last_trade_times[symbol] = current_time
            
    elif msg_type == "proposal":
        if "proposal" in data:
            proposal_id = data["proposal"]["id"]
            payout = data["proposal"]["ask_price"]
            ws.send(json.dumps({"buy": proposal_id, "price": float(payout) + 2}))
        else:
            print(f"Market Notice: {data.get('error', {}).get('message', '')}")
            
    elif msg_type == "buy":
        if "buy" in data:
            contract_id = data["buy"]["contract_id"]
            print(f"SUCCESS! Position opened! Contract ID: {contract_id}")
        elif "error" in data:
            print(f"Trade Execution Error: {data['error']['message']}")

def run_bot():
    while True:
        try:
            ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
            ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
            ws.run_forever()
        except Exception as e:
            print(f"Connection error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    run_bot()
