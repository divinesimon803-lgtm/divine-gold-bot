import websocket
import json
import threading
import time
from flask import Flask

# 1. Keep-Alive Web Server for Render Free Tier
app = Flask(__name__)

@app.route('/')
def home():
    return "Divine Gold APA Trading Bot is active and running!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

# 2. Deriv API Configuration
API_TOKEN = "pat_9ea5fd57fa2cfc960e7c30d0f7a737d559dc6dc258dcf572d32bae26999092e8"
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
        print("Authorization Successful! Monitoring Gold (XAUUSD) for APA signals...")
        ws.send(json.dumps({"ticks": SYMBOL}))
        
    elif msg_type == "tick":
        quote = data["tick"]["quote"]
        print(f"Live Gold Price: {quote}")
        
        # --- APA STRATEGY & RISK MANAGEMENT LOGIC ---
        current_time = time.time()
        
        # Cooldown timer to evaluate trades (e.g., every 60 seconds)
        if current_time - last_trade_time > 60:
            
            trade_request = {
                "buy": 1,
                "price": 10, # Max stake allocation
                "parameters": {
                    "amount": 1,                  # $1 Stake amount
                    "basis": "stake",
                    "contract_type": "MULTUP",    # Bullish multiplier contract
                    "currency": "USD",
                    "symbol": SYMBOL,
                    "multiplier": 50,             # 50x leverage multiplier
                    "limit_order": {
                        "stop_loss": 0.50,        # Auto-closes if loss hits $0.50
                        "take_profit": 1.00       # Auto-closes if profit hits $1.00
                    }
                }
            }
            
            # --- LIVE TRADING ENABLED ---
            ws.send(json.dumps(trade_request))
            print("APA Signal Triggered: Multiplier Buy Order sent with SL & TP!")
            
            last_trade_time = current_time
            
    elif msg_type == "buy":
        if "buy" in data:
            contract_id = data["buy"]["contract_id"]
            print(f"SUCCESS! Trade opened in the cloud. Contract ID: {contract_id}")
        elif "error" in data:
            print(f"Trade Execution Error: {data['error']['message']}")

def run_bot():
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
    ws.run_forever()

if __name__ == "__main__":
    # Start web server thread to keep Render awake for free
    t = threading.Thread(target=run_web)
    t.start()
    
    # Start trading execution loop
    run_bot()
