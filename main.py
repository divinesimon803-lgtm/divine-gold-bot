import websocket
import json
import time

# Your Deriv API Token
API_TOKEN = "pat_50a8ece94a33d9a1da08e00652a7586ce90cdaa4780682d84acfee7d0c0a540f"
APP_ID = "1089"  # Default public Deriv App ID
SYMBOL = "frxXAUUSD" # Gold on Deriv

def on_open(ws):
    print("Connected to Deriv API successfully!")
    auth_data = {"authorize": API_TOKEN}
    ws.send(json.dumps(auth_data))

def on_message(ws, message):
    data = json.loads(message)
    msg_type = data.get("msg_type")
    
    if msg_type == "authorize":
        print("Authorization Successful! Bot is now monitoring Gold (XAUUSD)...")
        # Subscribe to Gold ticks
        ws.send(json.dumps({"ticks": SYMBOL}))
        
    elif msg_type == "tick":
        quote = data["tick"]["quote"]
        print(f"Live Gold Price: {quote}")
        # APA / Price Action logic will execute here

def run_bot():
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
    ws.run_forever()

if __name__ == "__main__":
    run_bot()
