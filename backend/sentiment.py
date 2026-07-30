import sys
import json
import feedparser
import warnings
from urllib.parse import quote

# Suppress HuggingFace warnings
warnings.filterwarnings("ignore")

try:
    from transformers import pipeline
except ImportError:
    # If not installed yet or still installing, fallback safely
    pipeline = None

# Cache the pipeline globally so it doesn't reload heavily in loops
_sentiment_pipeline = None

def get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None and pipeline is not None:
        try:
            # FinBERT is specifically trained on financial text
            _sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert", device=-1)
        except Exception:
            pass
    return _sentiment_pipeline

def fetch_news(ticker):
    """Fetches recent news headlines for a ticker using Yahoo Finance RSS."""
    # Convert crypto to standard format if needed
    if 'USD' in ticker and '/' not in ticker:
        query = ticker.replace('USD', '-USD')
    elif '/' in ticker:
        query = ticker.replace('/', '-')
    else:
        query = ticker
        
    url = f"https://finance.yahoo.com/rss/headline?s={quote(query)}"
    feed = feedparser.parse(url)
    
    headlines = []
    for entry in feed.entries[:5]: # Get top 5 recent headlines
        headlines.append(entry.title)
    return headlines

def analyze_sentiment(ticker):
    """Returns a score between -1.0 (Extreme Fear) and 1.0 (Extreme Greed)"""
    headlines = fetch_news(ticker)
    
    if not headlines:
        return 0.0 # Neutral if no news
        
    pipe = get_sentiment_pipeline()
    if not pipe:
        # Fallback if transformers failed to load
        return 0.0
        
    results = pipe(headlines)
    
    total_score = 0.0
    for res in results:
        label = res['label'].lower()
        score = res['score']
        
        if label == 'positive':
            total_score += score
        elif label == 'negative':
            total_score -= score
        # neutral adds 0
        
    avg_score = total_score / len(headlines)
    return avg_score

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    try:
        score = analyze_sentiment(ticker)
        print(json.dumps({"ticker": ticker, "sentiment_score": score}))
    except Exception as e:
        print(json.dumps({"error": str(e), "sentiment_score": 0.0}))
