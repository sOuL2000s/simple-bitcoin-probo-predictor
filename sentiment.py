# sentiment.py (Fixed)

import feedparser
from textblob import TextBlob
import urllib.parse
import streamlit as st

def fetch_news_sentiment(query="bitcoin", max_items=20):
    encoded_query = urllib.parse.quote(query)  # URL encode the query
    url = f"https://news.google.com/rss/search?q={encoded_query}"
    
    feed = feedparser.parse(url)
    headlines = [entry.title for entry in feed.entries[:max_items]]

    if not headlines:
        return 0  # Neutral if no news

    sentiments = [TextBlob(headline).sentiment.polarity for headline in headlines]
    return round(sum(sentiments) / len(sentiments), 3)

@st.cache_data(ttl=600)
def get_bitcoin_sentiment():
    return fetch_news_sentiment("bitcoin OR btc")
