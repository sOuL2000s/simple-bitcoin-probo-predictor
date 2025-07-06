# probo_strategy.py

from btc_data import fetch_ohlcv, add_technical_indicators, get_current_price
from sentiment import get_bitcoin_sentiment

def interpret_market_conditions(df):
    latest = df.iloc[-1]
    rsi = latest["RSI"]
    ema_20 = latest["EMA_20"]
    ema_50 = latest["EMA_50"]

    # Trend signal
    bullish_trend = ema_20 > ema_50
    oversold = rsi < 30
    overbought = rsi > 70

    return {
        "bullish_trend": bullish_trend,
        "oversold": oversold,
        "overbought": overbought,
        "rsi": rsi,
        "ema_20": ema_20,
        "ema_50": ema_50
    }

def recommend_probo_vote():
    print("[+] Fetching market data...")
    df = fetch_ohlcv()
    df = add_technical_indicators(df)
    market = interpret_market_conditions(df)
    price = get_current_price()

    print("[+] Analyzing sentiment...")
    sentiment_score = get_bitcoin_sentiment()

    print("\n📊 BTC Market Snapshot")
    print(f"Price: ${price}")
    print(f"RSI: {market['rsi']:.2f} | EMA20: {market['ema_20']:.2f} | EMA50: {market['ema_50']:.2f}")
    print(f"Sentiment Score: {sentiment_score} ({'Bullish' if sentiment_score > 0 else 'Bearish' if sentiment_score < 0 else 'Neutral'})")

    # Decision logic
    vote = "NO"
    if market["bullish_trend"] and sentiment_score > 0:
        vote = "YES"
    elif market["oversold"] and sentiment_score > -0.1:
        vote = "YES"
    elif market["overbought"] and sentiment_score < 0:
        vote = "NO"

    print(f"\n🧠 Probo Recommendation: ✅ Vote {vote}")
    return vote

if __name__ == "__main__":
    recommend_probo_vote()
