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

API_TOKEN = "pat_9ea5fd57fa2cfc960e7c30d0f7a737d559dc6dc258dcf572d32bae26999092e8"
APP_ID = "1089" 
SYMBOL = "frxXAUUSD"

ws_global = None
last_trade_time = 0

def on_open(ws):
    global ws_global
    ws_global = ws
    print("Connected to Deriv API successfully!")
    auth_data = {"authorize": API_TOKEN}
    ws.send(json.dumps(auth_data))

def on_message(ws, message):
    global last_trade_time
    data = json.loads(message)
    msg_type = data.get("msg_type")
    
    if msg_type == "authorize":
        print("Authorization Successful! Requesting trade proposal for Gold...")
        # Request a proposal first (Deriv standard procedure)
        proposal_request = {
            "proposal": 1,
            "amount": 1,
            "basis": "stake",
            "contract_type": "MULTUP",
            "currency": "USD",
            "symbol": SYMBOL,
            "multiplier": 50,
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
            print(عf"Received Proposal ID: {proposal_id}. Buying contract now...")
            
            # Buy using the proposal ID
            buy_request = {
                "buy": proposal_id,
                "price": 2
            }
            ws.send(json.dumps(buy_request))
        else:
            print(f"Proposal Error: {data}")
            
    elif msg_type == "tick":
        quote = data["tick"]["quote"]
        print(f"Live Gold Price: {quote}")
        
        # Every 30 seconds, request a new proposal to keep executing trades
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
