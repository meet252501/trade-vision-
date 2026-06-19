"""
TradeVision AI — news_sentiment.py
Fetches news for a given ticker from Alpaca News API.
"""
import json
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"

try:
    from alpaca.data.historical.news import NewsClient
    from alpaca.data.requests import NewsRequest
    
    API_KEY = os.getenv("ALPACA_API_KEY")
    SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    
    news_client = NewsClient(API_KEY, SECRET_KEY)
    
    req = NewsRequest(
        symbols=[ticker],
        start=datetime.now() - timedelta(days=7),
        limit=8,
        sort="desc"
    )
    
    news = news_client.get_news(req)
    
    articles = []
    for article in news.news:
        # Simple sentiment heuristic based on keywords
        headline = article.headline or ""
        hl = headline.lower()
        
        sentiment = 0.0
        bullish_words = ["surge", "rally", "gain", "rise", "jump", "soar", "high", "record", "bull", "upgrade", "beat", "strong", "growth", "boost"]
        bearish_words = ["drop", "fall", "plunge", "crash", "decline", "low", "sell", "bear", "downgrade", "miss", "weak", "loss", "fear", "risk"]
        
        for w in bullish_words:
            if w in hl:
                sentiment += 0.25
        for w in bearish_words:
            if w in hl:
                sentiment -= 0.25
        
        sentiment = max(-1.0, min(1.0, sentiment))
        
        # Time ago
        if article.created_at:
            delta = datetime.now(article.created_at.tzinfo) - article.created_at
            hours = delta.total_seconds() / 3600
            if hours < 1:
                time_ago = f"{int(delta.total_seconds() / 60)}m ago"
            elif hours < 24:
                time_ago = f"{int(hours)}h ago"
            else:
                time_ago = f"{int(hours / 24)}d ago"
        else:
            time_ago = "recently"
        
        articles.append({
            "headline": headline,
            "source": article.source or "Market Wire",
            "sentiment": round(sentiment, 2),
            "time": time_ago,
            "url": article.url or "",
            "symbols": [str(s) for s in (article.symbols or [])]
        })
    
    print(json.dumps(articles))

except Exception as e:
    # Fallback with empty array
    print(json.dumps([]))
