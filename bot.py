import ccxt
import pandas as pd
import requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===============================
# 🤖 BOT SOURCE
# ===============================
BOT_SOURCE = "GITHUB_ACTIONS"

# ===============================
# 🔐 TELEGRAM (UNCHANGED)
# ===============================
TOKEN = "8364584748:AAFeym3et4zJwmdKRxYtP3ieIKV8FuPWdQ8"
CHAT_ID = "@Tradecocom"

# ===============================
# ⚙️ SETTINGS
# ===============================
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

EMA_FAST = 20
EMA_SLOW = 50

# ===============================
# 🔁 EXCHANGE (FREE MEXC)
# ===============================
exchange = ccxt.mexc({
    "enableRateLimit": True
})

# ===============================
# 📨 TELEGRAM ALERT
# ===============================
def send_alert(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": message
            }
        )
    except:
        pass

# ===============================
# 📊 FETCH OHLCV (MINIMAL)
# ===============================
def fetch_data(symbol, timeframe):
    candles = exchange.fetch_ohlcv(
        symbol,
        timeframe=timeframe,
        limit=EMA_SLOW + 5
    )
    return pd.DataFrame(
        candles,
        columns=["time", "open", "high", "low", "close", "volume"]
    )

# ===============================
# 🚀 EMA CROSS CHECK (CLOSED CANDLE)
# ===============================
def check_signal(symbol, timeframe):
    df = fetch_data(symbol, timeframe)

    close = df["close"]

    ema_fast = close.ewm(span=EMA_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=EMA_SLOW, adjust=False).mean()

    # ✅ ONLY CLOSED CANDLES
    prev_fast = ema_fast.iloc[-3]
    prev_slow = ema_slow.iloc[-3]
    curr_fast = ema_fast.iloc[-2]
    curr_slow = ema_slow.iloc[-2]

    price = close.iloc[-2]
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if prev_fast < prev_slow and curr_fast > curr_slow:
        send_alert(
            f"🟢 BUY | EMA 20 Cross Above EMA 50\n\n"
            f"🤖 Source: {BOT_SOURCE}\n"
            f"📊 Pair: {symbol}\n"
            f"⏱ Timeframe: {timeframe}\n"
            f"💰 Price: {price}\n"
            f"🕒 UTC: {utc}"
        )

    elif prev_fast > prev_slow and curr_fast < curr_slow:
        send_alert(
            f"🔴 SELL | EMA 20 Cross Below EMA 50\n\n"
            f"🤖 Source: {BOT_SOURCE}\n"
            f"📊 Pair: {symbol}\n"
            f"⏱ Timeframe: {timeframe}\n"
            f"💰 Price: {price}\n"
            f"🕒 UTC: {utc}"
        )

# ===============================
# ▶️ MAIN
# ===============================
def main():
    # Start message (once per run)
    send_alert("✅ Crypto Signal Bot started successfully")

    with ThreadPoolExecutor(max_workers=6) as executor:
        tasks = [
            executor.submit(check_signal, pair, tf)
            for pair in PAIRS
            for tf in TIMEFRAMES
        ]
        for _ in as_completed(tasks):
            pass

if __name__ == "__main__":
    main()
    
