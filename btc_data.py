# btc_data.py

import requests
import pandas as pd
import time
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

BINANCE_BASE_URL = "https://api.binance.com"

def fetch_ohlcv(symbol="BTCUSDT", interval="1h", limit=100):
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base_vol", "taker_buy_quote_vol", "ignore"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df.astype(float)

    return df[["open", "high", "low", "close", "volume"]]

def add_technical_indicators(df):
    rsi = RSIIndicator(df["close"], window=14).rsi()
    ema_20 = EMAIndicator(df["close"], window=20).ema_indicator()
    ema_50 = EMAIndicator(df["close"], window=50).ema_indicator()

    df["RSI"] = rsi
    df["EMA_20"] = ema_20
    df["EMA_50"] = ema_50
    return df

def get_current_price(symbol="BTCUSDT"):
    url = f"{BINANCE_BASE_URL}/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    return float(response.json()["price"])

if __name__ == "__main__":
    df = fetch_ohlcv()
    df = add_technical_indicators(df)
    print(df.tail())
    print(f"Current BTC Price: ${get_current_price()}")
