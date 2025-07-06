# app.py

import streamlit as st
import plotly.graph_objects as go
from btc_data import fetch_ohlcv, add_technical_indicators, get_current_price
from sentiment import get_bitcoin_sentiment
from probo_strategy import interpret_market_conditions
from predictor import recommend_probo_vote_for_target
from telegram_bot import send_telegram_alert
from datetime import datetime, timedelta

st.set_page_config(page_title="BTC Probo Predictor", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @media (max-width: 600px) {
        .css-18ni7ap { padding-left: 0.5rem; padding-right: 0.5rem; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("📲 BTC Probo Predictor (Mobile Friendly)")

# Fetch market data
with st.spinner("Loading BTC data..."):
    df = fetch_ohlcv()
    df = add_technical_indicators(df)
    current_price = get_current_price()
    sentiment_score = get_bitcoin_sentiment()
    market = interpret_market_conditions(df)

st.metric("💰 BTC Price", f"${current_price:,.2f}")
st.markdown("---")

# 📥 Prediction form
st.subheader("🔮 Predict Probo Outcome")
with st.form("predict_form"):
    col1, col2 = st.columns(2)
    with col1:
        target_price = st.number_input("Target Price (USDT)", value=65000)
    with col2:
        target_time_str = st.text_input("Target Time (HH:MM in IST)", value="23:00")

    predict = st.form_submit_button("Get Recommendation")

if predict:
    try:
        # Convert IST time to UTC
        ist_time = datetime.strptime(target_time_str.strip(), "%H:%M")
        now_utc = datetime.utcnow()
        today_ist = now_utc + timedelta(hours=5.5)
        target_time_ist = today_ist.replace(hour=ist_time.hour, minute=ist_time.minute, second=0, microsecond=0)
        target_time_utc = target_time_ist - timedelta(hours=5.5)
        parsed_time = target_time_utc.strftime("%H:%M")

        # Run prediction
        result = recommend_probo_vote_for_target(target_price, parsed_time)

        # Display summary
        with st.expander("📊 Prediction Summary", expanded=True):
            st.markdown(f"**Current Price:** ${result['current_price']}")
            st.markdown(f"**Avg Δ/hr:** ${result['avg_delta_per_hour']}")
            st.markdown(f"**Time Left:** {result['hours_remaining']} hr(s)")
            st.markdown(f"**Projected Price:** ${result['projected_price']}")
            st.markdown(f"**Sentiment Score:** {result['sentiment']}")
            st.markdown(f"**Target Time (IST):** {target_time_str}")

        st.success(f"🧠 Recommended Vote: **{result['vote']}**")

        # Send Telegram Alert
        alert_message = (
            f"📣 *BTC Probo Vote Recommendation*\n"
            f"🕒 Target Time (IST): *{target_time_str}*\n"
            f"🎯 Target Price: *${result['target_price']}*\n"
            f"💰 Current: *${result['current_price']}*\n"
            f"📈 Projected: *${result['projected_price']}*\n"
            f"💬 Sentiment: *{result['sentiment']}*\n"
            f"✅ Vote: *{result['vote']}*"
        )
        send_telegram_alert(alert_message)

    except ValueError:
        st.error("❌ Invalid time format. Please enter as HH:MM in 24-hour IST.")

# 📈 Technicals
with st.expander("🧪 Technical Indicators"):
    col1, col2, col3 = st.columns(3)
    col1.metric("RSI", f"{market['rsi']:.2f}")
    col2.metric("EMA 20", f"{market['ema_20']:.2f}")
    col3.metric("EMA 50", f"{market['ema_50']:.2f}")
    st.markdown(
        f"**Trend**: {'📈 Uptrend' if market['bullish_trend'] else '📉 Downtrend'}  \n"
        f"**RSI Zone**: {'🔥 Overbought' if market['overbought'] else '🧊 Oversold' if market['oversold'] else '✅ Neutral'}"
    )

# 📊 Chart
with st.expander("📊 View Chart"):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"], name="Candles"))
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA_20"], mode='lines', name='EMA 20'))
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA_50"], mode='lines', name='EMA 50'))
    fig.update_layout(height=400, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
