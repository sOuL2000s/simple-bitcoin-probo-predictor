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

        # Calculate hours remaining for advice logic
        time_diff = target_time_utc - now_utc
        hours_remaining_float = time_diff.total_seconds() / 3600.0

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

        # --- Integrate Trust/Caution Logic to generate advice string ---
        trust_signals = 0
        caution_flags = 0
        advice_summary = [] # To collect advice for the Telegram message

        # Evaluate Trust Conditions
        if hours_remaining_float < 2:
            trust_signals += 1
        if market['bullish_trend'] or (market['ema_20'] < market['ema_50'] and df['close'].iloc[-1] < df['EMA_20'].iloc[-1]):
            trust_signals += 1
        if abs(sentiment_score) > 0.2:
            trust_signals += 1
        if 30 <= market['rsi'] <= 70:
            trust_signals += 1

        # Evaluate Caution Conditions
        if hours_remaining_float > 3:
            caution_flags += 1
        if market['overbought'] or market['oversold']:
            caution_flags += 1
        if abs(sentiment_score) < 0.05:
            caution_flags += 1

        # Determine the final advice string
        if trust_signals >= 3 and caution_flags < 2:
            advice_summary.append("🔐 Confidence: *GO with the vote!* (Trust: {}/5, Caution: {}/5)".format(trust_signals, caution_flags))
        elif caution_flags >= 2:
            advice_summary.append("🔐 Confidence: *SKIP the trade or WAIT!* (Trust: {}/5, Caution: {}/5)".format(trust_signals, caution_flags))
        else:
            advice_summary.append("🔐 Confidence: *Proceed with caution or wait for clearer signals.* (Trust: {}/5, Caution: {}/5)".format(trust_signals, caution_flags))

        # Display advice in Streamlit (remains the same)
        st.markdown("---")
        st.subheader("💡 Prediction Confidence Advisor")
        st.markdown("#### ✅ Trust Signals:")
        st.markdown(f"- Time to expiry is < 2 hours: {'**YES**' if hours_remaining_float < 2 else '**NO**'}")
        st.markdown(f"- BTC is trending cleanly (up or down): {'**YES**' if market['bullish_trend'] or (market['ema_20'] < market['ema_50'] and df['close'].iloc[-1] < df['EMA_20'].iloc[-1]) else '**NO** (Trend unclear/Choppy)'}")
        st.markdown(f"- Sentiment score is strongly positive/negative (>0.2): {'**YES**' if abs(sentiment_score) > 0.2 else '**NO**'} (Score: {sentiment_score:.2f})")
        st.markdown(f"- RSI is not extreme (30-70): {'**YES**' if 30 <= market['rsi'] <= 70 else '**NO**'} (RSI: {market['rsi']:.2f})")
        st.markdown("- No major news expected: *Requires manual check*")
        st.markdown("- Candle bodies are stable (not huge wicks): *Requires visual inspection of chart*")

        st.markdown("#### ⚠️ Caution Flags:")
        st.markdown(f"- Target time is > 3 hours away: {'**YES**' if hours_remaining_float > 3 else '**NO**'}")
        st.markdown("- BTC just made a massive move: *Requires manual check/recent price analysis*")
        st.markdown(f"- RSI is > 75 or < 25: {'**YES**' if market['overbought'] or market['oversold'] else '**NO**'} (RSI: {market['rsi']:.2f})")
        st.markdown(f"- Sentiment is conflicting (score ≈ 0): {'**YES**' if abs(sentiment_score) < 0.05 else '**NO**'} (Score: {sentiment_score:.2f})")
        st.markdown("- Big news coming (Fed rate hike, CPI data): *Requires manual check of news calendar*")
        st.markdown("- Candle volatility is high (huge wicks): *Requires visual inspection of chart*")

        st.markdown("---")
        st.markdown(f"**Total Trust Signals Met**: {trust_signals}")
        st.markdown(f"**Total Caution Flags Present**: {caution_flags}")

        if trust_signals >= 3 and caution_flags < 2:
            st.success("🔐 Pro Tip: At least 3 'Trust' signals align. **GO with the vote!**")
        elif caution_flags >= 2:
            st.warning("🔐 Pro Tip: 2+ 'Caution' flags are present. **SKIP the trade or WAIT!**")
        else:
            st.info("🔐 Pro Tip: Conditions are mixed. **Proceed with caution or wait for clearer signals.**")


        # Send Telegram Alert with advice
        advice_str = "\n".join(advice_summary)
        alert_message = (
            f"📣 *BTC Probo Vote Recommendation*\n"
            f"🕒 Target Time (IST): *{target_time_str}*\n"
            f"🎯 Target Price: *${result['target_price']}*\n"
            f"💰 Current: *${result['current_price']}*\n"
            f"📈 Projected: *${result['projected_price']}*\n"
            f"💬 Sentiment: *{result['sentiment']}*\n"
            f"✅ Vote: *{result['vote']}*\n"
            f"\n--- Confidence Advisor ---\n"
            f"{advice_str}"
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

# Add the original "Cheat Sheet" as informational sections
st.markdown("---")
st.subheader("🧠 BTC Probo Prediction Cheat Sheet Reference")

st.markdown("This section provides the original guidelines for reference.")

st.markdown("### ✅ TRUST the Prediction When:")
st.markdown("""
- **Condition**: Time to expiry is < 2 hours
    - **Why**: Short-term moves are easier to project with recent trend/sentiment
- **Condition**: BTC is trending cleanly (up or down)
    - **Why**: EMA crossover + delta will align clearly
- **Condition**: Sentiment score is strongly positive/negative (>0.2)
    - **Why**: Clear market direction from sentiment
- **Condition**: RSI is not extreme (30–70)
    - **Why**: Means no strong mean-reversion counterforces
- **Condition**: No major news expected
    - **Why**: Market moves more "technically" in news-free windows
- **Condition**: Candle bodies are stable (not huge wicks)
    - **Why**: Less noise = better delta prediction accuracy
""")

st.markdown("### ⚠️ BE CAUTIOUS / DOUBLE-CHECK When:")
st.markdown("""
- **Red Flag**: Target time is > 3 hours away
    - **Why**: Market conditions may shift unpredictably
- **Red Flag**: BTC just made a massive move
    - **Why**: Mean reversion likely → momentum may reverse
- **Red Flag**: RSI is > 75 or < 25
    - **Why**: Overbought/oversold zones are prone to reversals
- **Red Flag**: Sentiment is conflicting (score ≈ 0)
    - **Why**: Market indecisive — avoid betting
- **Red Flag**: Big news coming (Fed rate hike, CPI data)
    - **Why**: Trends and sentiment can break instantly
- **Red Flag**: Candle volatility is high (huge wicks)
    - **Why**: Delta estimates become noisy and inaccurate
""")

st.markdown("### 🔐 Pro Tip (Original Reference):")
st.markdown("""
If at least 3/5 “Trust” signals align → GO with the vote.
If 2+ “Caution” flags are present → SKIP the trade or wait.
""")

st.markdown("### ✅ Example: When to TRUST (Original Reference)")
st.markdown("""
- Time: 1 hour left
- BTC uptrending
- EMA20 > EMA50
- RSI = 58
- Sentiment = +0.3

→ ✅ Trust YES vote
""")

st.markdown("### ⚠️ Example: When to AVOID (Original Reference)")
st.markdown("""
- Time: 4 hours left
- BTC dumped $800 in 15 mins
- RSI = 22
- Sentiment = 0.05

→ ⚠️ Avoid vote — unpredictable zone
""")