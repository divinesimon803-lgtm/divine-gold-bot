import websocket
import json
import threading
from flask import Flask

# Tiny web server to satisfy Render's Web Service requirement and keep the bot awake for free
app = Flask(__name__)

@app.route('/')
def home():
    return "Divine Gold Bot is active and running!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

# Deriv API Configuration
API_TOKEN = "pat_9ea5fd57fa2cfc960e7c30d0f7a737d559dc6dc258dcf572d32bae26999092e8"
APP_ID = "1089" 
SYMBOL = "frxXAUUSD"

def on_open(ws):
    print("Connected to Deriv API successfully!")
    auth_data = {"authorize": API_TOKEN}
    ws.send(json.dumps(auth_data))

def on_message(ws, message):
    data = json.loads(message)
    msg_type = data.get("msg_type")
    
    if msg_type == "authorize":
        print("Authorization Successful! Monitoring Gold (XAUUSD)...")
        ws.send(json.dumps({"ticks": SYMBOL}))
        
    elif msg_type == "tick":
        quote = data["tick"]["quote"]
        print(f"Live Gold Price: {quote}")

def run_bot():
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
    ws.run_forever()

if __name__ == "__main__":
    # Start the tiny web server in the background thread so Render is happy
    t = threading.Thread(target=run_web)
    t.start()
    
    # Start the trading bot
    run_bot()
