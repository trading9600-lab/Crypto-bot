import ccxt
import pandas as pd
import requests
from datetime import datetime, timezone

# ===============================
# 🤖 BOT SOURCE
# ===============================
BOT_SOURCE = "GitHub Actions"

# ===============================
# 🔐 TELEGRAM (UNCHANGED)
# ===============================
TOKEN = "8364584748:AAFeym3et4zJwmdKRxYtP3ieIKV8FuPWdQ8"
CHAT_ID = "@Tradecocom"

# ===============================
# ⚙️ SETTINGS (UNCHANGED)
# ===============================
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

EMA_FAST = 20
EMA_SLOW = 50

# ===============================
# 🔁 EXCHANGE
# ===============================
exchange = ccxt.mexc({
    "enableRateLimit": True
})

# ===============================
# 📨 TELEGRAM SEND
# ===============================
def send_alert(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text
    })

# ===============================
# 📊 FETCH DATA
# ===============================
def get_data(symbol, timeframe):
    candles = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
    return pd.DataFrame(
        candles,
        columns=["time", "open", "high", "low", "close", "volume"]
    )

# ===============================
# 🚨 EMA CROSS (-1 / -2 FAST)
# ===============================
def check_signal(symbol, timeframe):
    df = get_data(symbol, timeframe)

    df["ema_fast"] = df["close"].ewm(span=EMA_FAST).mean()
    df["ema_slow"] = df["close"].ewm(span=EMA_SLOW).mean()

    prev_fast = df["ema_fast"].iloc[-2]
    prev_slow = df["ema_slow"].iloc[-2]
    curr_fast = df["ema_fast"].iloc[-1]
    curr_slow = df["ema_slow"].iloc[-1]

    price = df["close"].iloc[-1]

    signal = None

    if prev_fast < prev_slow and curr_fast > curr_slow:
        signal = "🟢 BUY EMA CROSS (EARLY)"
    elif prev_fast > prev_slow and curr_fast < curr_slow:
        signal = "🔴 SELL EMA CROSS (EARLY)"

    if signal:
        message = (
            f"{signal}\n\n"
            f"🤖 Source: {BOT_SOURCE}\n\n"
            f"📊 Pair: {symbol}\n"
            f"⏱ Timeframe: {timeframe}\n"
            f"💰 Price: {price}\n"
            f"⚠️ Running candle (-1)\n"
            f"🕒 UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        send_alert(message)

# ===============================
# ▶️ MAIN
# ===============================
def main():
    send_alert(
        "✅ Crypto EMA Signal Bot Started\n\n"
        f"🤖 Source: {BOT_SOURCE}\n"
        "⚡ Mode: Fast (-1 / -2 EMA crossover)"
    )

    for pair in PAIRS:
        for tf in TIMEFRAMES:
            try:
                check_signal(pair, tf)
            except Exception as e:
                print(f"Error {pair} {tf}: {e}")

if __name__ == "__main__":
    main()
    
