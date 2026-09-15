import websocket
import json
import threading
import time
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Divine Gold APA Trading Bot is active!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

API_TOKEN = "pat_50a8ece94a33d9a1da08e00652a7586ce90cdaa4780682d84acfee7d0c0a540f"
APP_ID = "1089" 
SYMBOL = "frxXAUUSD"

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
        print("Authorization Successful! Requesting trade proposal with correct platform...")
        proposal_request = {
            "proposal": 1,
            "amount": 1,
            "basis": "stake",
            "contract_type": "MULTUP",
            "currency": "USD",
            "symbol": SYMBOL,
            "multiplier": 50,
            "passthrough": {"platform": "deriv_trader"},
            "limit_order": {
                "stop_loss": 0.50,
                "take_profit": 1.00
            }
        }
        ws.send(json.dumps(proposal_request))
        ws.send(json.dumps({"ticks": SYMBOL}))
        
    elif msg_type == "proposal":
        if "proposal" in data:
            proposal_id = data["proposal"]["id"]
            print(f"Received Proposal ID: {proposal_id}. Executing live trade...")
            
            buy_request = {
                "buy": proposal_id,
                "price": 2
            }
            ws.send(json.dumps(buy_request))
        else:
            print(f"Proposal Details / Error: {data}")
            
    elif msg_type == "tick":
        quote = data["tick"]["quote"]
        print(f"Live Gold Price: {quote}")
        
        current_time = time.time()
        if current_time - last_trade_time > 30:
            proposal_request = {
                "proposal": 1,
                "amount": 1,
                "basis": "stake",
                "contract_type": "MULTUP",
                "currency": "USD",
                "symbol": SYMBOL,
                "multiplier": 50,
                "passthrough": {"platform": "deriv_trader"},
                "limit_order": {
                    "stop_loss": 0.50,
                    "take_profit": 1.00
                }
            }
            ws.send(json.dumps(proposal_request))
            last_trade_time = current_time

    elif msg_type == "buy":
        if "buy" in data:
            contract_id = data["buy"]["contract_id"]
            print(f"SUCCESS! Live trade opened! Contract ID: {contract_id}")
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
