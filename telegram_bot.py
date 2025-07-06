# telegram_bot.py

import requests

# Your bot token and user ID
BOT_TOKEN = "7961650111:AAEUAwXv16l3Pb_9EFT_Umy0fYNjN5ijAqU"
USER_ID = 5368095453  # You can also use your numeric ID if this fails

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": USER_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Telegram alert sent successfully.")
        else:
            print("Failed to send alert:", response.text)
    except Exception as e:
        print("Telegram alert error:", str(e))

# Test message
if __name__ == "__main__":
    send_telegram_alert("🚨 Test alert from BTC Probo Predictor!")
