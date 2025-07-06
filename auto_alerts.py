import threading, schedule, time
from flask import Flask
from datetime import datetime, timedelta
from btc_data import get_current_price
from predictor import recommend_probo_vote_for_target
from telegram_bot import send_telegram_alert

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ BTC Auto Alert Bot Running (IST)"

def get_next_10_min_block_ist():
    now_utc = datetime.utcnow()
    ist_now = now_utc + timedelta(hours=5, minutes=30)

    # Round up to next HH:m0
    next_min = (ist_now.minute // 10 + 1) * 10
    if next_min == 60:
        ist_target = ist_now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        ist_target = ist_now.replace(minute=next_min, second=0, microsecond=0)

    # Convert IST → UTC for backend use
    target_time_utc = ist_target - timedelta(hours=5, minutes=30)
    return target_time_utc.strftime("%H:%M"), ist_target.strftime("%H:%M")

def send_prediction():
    target_time_utc, target_time_ist = get_next_10_min_block_ist()

    result = recommend_probo_vote_for_target(target_price=64000, target_time_str=target_time_utc)

    message = (
        f"📣 *BTC Auto Vote Alert*\n"
        f"🕒 Target Time (IST): *{target_time_ist}*\n"
        f"📈 Projected: *${result['projected_price']}*\n"
        f"💬 Sentiment: *{result['sentiment']}*\n"
        f"✅ Vote: *{result['vote']}*"
    )
    send_telegram_alert(message)

def run_schedule():
    schedule.every(10).minutes.do(send_prediction)
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_schedule).start()
run_flask()
