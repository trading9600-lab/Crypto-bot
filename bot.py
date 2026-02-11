import ccxt
import pandas as pd
import requests
import json
import os
from datetime import datetime, timezone, timedelta

# ===============================
# 🤖 BOT SOURCE
# ===============================
BOT_SOURCE = "GitHub Actions"

# ===============================
# 🔐 TELEGRAM
# ===============================
TOKEN = "8364584748:AAFeym3et4zJwmdKRxYtP3ieIKV8FuPWdQ8"
CHAT_ID = "@Tradecocom"

# ===============================
# ⚙️ SETTINGS
# ===============================
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h"]

EMA_FAST = 20
EMA_SLOW = 50
COOLDOWN_MINUTES = 10
MIN_CANDLES_REQUIRED = 100

STATE_FILE = "signal_state.json"

# ===============================
# 🔁 EXCHANGE
# ===============================
exchange = ccxt.mexc({
    "enableRateLimit": True
})

# ===============================
# 📂 STATE MANAGEMENT
# ===============================
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ===============================
# 📩 TELEGRAM
# ===============================
def send_alert(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=15)
    except:
        pass

# ===============================
# 📊 FETCH DATA
# ===============================
def get_data(symbol, timeframe):
    try:
        candles = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(
            candles,
            columns=["time", "open", "high", "low", "close", "volume"]
        )
        return df
    except:
        return None

# ===============================
# 🚨 FRESH CROSSOVER CHECK
# ===============================
def check_signal(symbol, timeframe, state):

    df = get_data(symbol, timeframe)
    if df is None or len(df) < MIN_CANDLES_REQUIRED:
        return

    df["ema_fast"] = df["close"].ewm(span=EMA_FAST, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=EMA_SLOW, adjust=False).mean()

    # Use CLOSED candles only (clean)
    prev_fast = df["ema_fast"].iloc[-3]
    prev_slow = df["ema_slow"].iloc[-3]
    curr_fast = df["ema_fast"].iloc[-2]
    curr_slow = df["ema_slow"].iloc[-2]

    price = df["close"].iloc[-2]
    candle_time = df["time"].iloc[-2]

    signal = None

    # Detect fresh cross
    if prev_fast < prev_slow and curr_fast > curr_slow:
        signal = "BUY"
    elif prev_fast > prev_slow and curr_fast < curr_slow:
        signal = "SELL"

    if not signal:
        return

    key = f"{symbol}_{timeframe}"
    now = datetime.now(timezone.utc)

    # Prevent duplicates + cooldown
    if key in state:
        last_signal_time = datetime.fromisoformat(state[key]["alert_time"])
        last_candle_time = state[key]["candle_time"]

        # Same candle already alerted
        if str(candle_time) == last_candle_time:
            return

        # Cooldown protection
        if now - last_signal_time < timedelta(minutes=COOLDOWN_MINUTES):
            return

    # Save state
    state[key] = {
        "type": signal,
        "alert_time": now.isoformat(),
        "candle_time": str(candle_time)
    }

    message = (
        f"{'🟢 BUY EMA CROSS' if signal=='BUY' else '🔴 SELL EMA CROSS'}\n\n"
        f"🤖 Source: {BOT_SOURCE}\n\n"
        f"📊 Pair: {symbol}\n"
        f"⏱ Timeframe: {timeframe}\n"
        f"💰 Price: {price}\n"
        f"🕒 UTC: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    send_alert(message)

# ===============================
# ▶️ MAIN
# ===============================
def main():

    state = load_state()

    send_alert(
        "✅ Crypto EMA Cross Bot Started\n\n"
        f"🤖 Source: {BOT_SOURCE}\n"
        "📊 Strategy: EMA 20 / 50 Fresh Crossover\n"
        "🛡 Min Candles: 100\n"
        "⏳ Cooldown: 10 Minutes\n"
        f"🕒 UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    for pair in PAIRS:
        for tf in TIMEFRAMES:
            check_signal(pair, tf, state)

    save_state(state)

if __name__ == "__main__":
    main()
    
