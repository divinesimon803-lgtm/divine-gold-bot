import websocket
import json
import threading
import time
import random
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Divine Multi-Pair Profit Bot is active!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

API_TOKEN = "pat_9ea5fd57fa2cfc960e7c30d0f7a737d559dc6dc258dcf572d32bae26999092e8"
APP_ID = "1089" 

# Multiple pairs with Gold (frxXAUUSD) as the main focus
SYMBOLS = [
    {"symbol": "frxXAUUSD", "weight": "main"},
    {"symbol": "frxEURUSD", "weight": "sub"},
    {"symbol": "frxGBPUSD", "weight": "sub"},
    {"symbol": "frxAUDUSD", "weight": "sub"},
    {"symbol": "frxUSDJPY", "weight": "sub"}
]

def run_symbol_bot(symbol_info):
    symbol = symbol_info["symbol"]
    is_main = symbol_info["weight"] == "main"
    
    def on_open(ws):
        print(f"Connected to Deriv API for {symbol}!")
        ws.send(json.dumps({"authorize": API_TOKEN}))

    def on_message(ws, message):
        data = json.loads(message)
        msg_type = data.get("msg_type")
        
        if msg_type == "authorize":
            print(f"Authorized for {symbol}. Subscribing to ticks...")
            ws.send(json.dumps({"ticks": symbol}))
            
        elif msg_type == "tick":
            # Main asset (Gold) gets priority/faster cycle, others get spaced out
            sleep_time = 15 if is_main else 30
            if random.random() < 0.3: # Random trigger condition for multi-trade spread
                chosen_stake = random.choice([1, 2, 3])
                chosen_multiplier = 50 if chosen_stake == 1 else 100
                
                print(f"[{symbol}] Setup found! Stake: ${chosen_stake}, Multiplier: {chosen_multiplier}x")
                
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
                time.sleep(sleep_time)
                
        elif msg_type == "proposal":
            if "proposal" in data:
                proposal_id = data["proposal"]["id"]
                payout = data["proposal"]["ask_price"]
                ws.send(json.dumps({"buy": proposal_id, "price": float(payout) + 2}))
                
        elif msg_type == "buy":
            if "buy" in data:
                print(f"SUCCESS! Trade opened on {symbol}! Contract ID: {data['buy']['contract_id']}")

    def start_ws():
        while True:
            try:
                ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
                ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
                ws.run_forever()
            except Exception as e:
                print(f"Connection error on {symbol}: {e}")
                time.sleep(5)

    start_ws()

if __name__ == "__main__":
    # Start web server keep-alive thread
    t_web = threading.Thread(target=run_web)
    t_web.start()
    
    # Launch individual background threads for each currency pair simultaneously
    for item in SYMBOLS:
        t = threading.Thread(target=run_symbol_bot, args=(item,))
        t.daemon = True
        t.start()
        time.sleep(1) # Stagger connections slightly
        
    # Keep main thread alive
    while True:
        time.sleep(60)
