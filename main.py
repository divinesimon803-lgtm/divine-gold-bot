import websocket
import json
import threading
import time
import random
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Divine Gold & Volatility Bot is active!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

API_TOKEN = "pat_9ea5fd57fa2cfc960e7c30d0f7a737d559dc6dc258dcf572d32bae26999092e8"
APP_ID = "1089" 
# Using Volatility 75 Index (R_75) which runs 24/7 and accepts web multipliers instantly
SYMBOL = "R_75" 

last_trade_time = 0

def on_open(ws):
    print("Connected to Deriv API successfully!")
    auth_data = {"authorize": API_TOKEN}
    ws.send(json.dumps(auth_data))

def on_message(ws, message):
    global last_trade_time
    data = json.loads(message)
    msg_type = data.get("msg_type")
    
    if msg_type == "authorize":
        print(f"Authorization Successful! Locking onto {SYMBOL} for 24/7 automated execution...")
        ws.send(json.dumps({"ticks": SYMBOL}))
        
    elif msg_type == "tick":
        quote = data["tick"]["quote"]
        print(f"Live Price ({SYMBOL}): {quote}")
        
        # Every 30 seconds, evaluate for a trade with dynamic variable sizing
        current_time = time.time()
        if current_time - last_trade_time > 30:
            
            chosen_stake = random.choice([1, 2, 3]) 
            chosen_multiplier = 50 if chosen_stake == 1 else 100
            
            print(f"Signal Evaluated. Dynamic Stake: ${chosen_stake} with {chosen_multiplier}x multiplier.")
            
            proposal_request = {
                "proposal": 1,
                "amount": chosen_stake,
                "basis": "stake",
                "contract_type": "MULTUP",
                "currency": "USD",
                "symbol": SYMBOL,
                "multiplier": chosen_multiplier,
                "limit_order": {
                    "stop_loss": round(chosen_stake * 0.5, 2),
                    "take_profit": round(chosen_stake * 1.0, 2)
                }
            }
            ws.send(json.dumps(proposal_request))
            last_trade_time = current_time
            
    elif msg_type == "proposal":
        if "proposal" in data:
            proposal_id = data["proposal"]["id"]
            payout = data["proposal"]["ask_price"]
            print(f"Proposal ID received: {proposal_id}. Executing order...")
            
            buy_request = {
                "buy": proposal_id,
                "price": float(payout) + 2
            }
            ws.send(json.dumps(buy_request))
        else:
            print(f"Proposal Notice: {data.get('error', {}).get('message', data)}")
            
    elif msg_type == "buy":
        if "buy" in data:
            contract_id = data["buy"]["contract_id"]
            print(f"SUCCESS! Automated trade opened! Contract ID: {contract_id}")
        elif "error" in data:
            print(f"Trade Execution Error: {data['error']['message']}")

def run_bot():
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
    ws.run_forever()

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    run_bot()
