# predictor.py

from btc_data import fetch_ohlcv, add_technical_indicators, get_current_price
from sentiment import get_bitcoin_sentiment
import datetime

def predict_future_price(hours_ahead=1):
    df = fetch_ohlcv(interval="1h", limit=10)
    df = add_technical_indicators(df)

    # Calculate avg price movement per hour
    df["price_change"] = df["close"].diff()
    avg_delta = df["price_change"].mean()

    current_price = get_current_price()
    projected_price = current_price + (avg_delta * hours_ahead)

    return round(projected_price, 2), round(avg_delta, 2), current_price

def recommend_probo_vote_for_target(target_price, target_time_str):
    # 1. Parse time and calculate hours remaining
    now = datetime.datetime.utcnow()
    target_time = datetime.datetime.strptime(target_time_str, "%H:%M")
    target_time = now.replace(hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
    
    if target_time < now:
        target_time += datetime.timedelta(days=1)

    hours_remaining = (target_time - now).total_seconds() / 3600
    hours_remaining = max(0.25, round(hours_remaining, 2))  # Minimum 15 min window

    # 2. Get sentiment
    sentiment = get_bitcoin_sentiment()

    # 3. Predict price
    projected, delta, current = predict_future_price(hours_remaining)

    # 4. Decision logic
    if projected >= target_price and sentiment >= -0.1:
        vote = "YES"
    else:
        vote = "NO"

    # 5. Return analysis
    result = {
        "current_price": current,
        "avg_delta_per_hour": delta,
        "hours_remaining": hours_remaining,
        "projected_price": projected,
        "sentiment": sentiment,
        "target_price": target_price,
        "target_time": target_time.strftime("%H:%M"),
        "vote": vote
    }

    return result

if __name__ == "__main__":
    # Sample example:
    question = recommend_probo_vote_for_target(target_price=63500, target_time_str="23:00")
    
    print("\n🧠 Prediction Summary:")
    for k, v in question.items():
        print(f"{k.replace('_', ' ').title()}: {v}")
