import praw
import requests
import pandas as pd
import yaml
import re
import os
from datetime import datetime, timedelta, timezone
import yfinance as yf  # Needed for ticker_to_company

class SentimentFetcher:
    """Fetches sentiment data from Reddit and NewsAPI with in-memory caching."""
    
    def __init__(self, config_path: str = None):
        """Initialize APIs and cache."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "settings.yaml")
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Reddit config
        reddit_config = config['reddit']
        self.reddit = praw.Reddit(
            client_id=reddit_config['client_id'],
            client_secret=reddit_config['client_secret'],
            username=reddit_config['username'],
            password=reddit_config['password'],
            user_agent=reddit_config['user_agent']
        )
        
        # NewsAPI
        self.newsapi_key = config['newsapi']['api_key']
        self.newsapi_url = "https://newsapi.org/v2/everything"
        
        self.cache = {}
    
    def fetch_sentiment_data(self, ticker: str, period: str = "7d", 
                             subreddits: list = None, 
                             news_sources: list = None) -> pd.DataFrame:
        """
        Fetch sentiment data from Reddit and NewsAPI for a given ticker.
        """
        if subreddits is None:
            subreddits = ["wallstreetbets", "stocks", "investing","StockMarket", "finance"]
        if news_sources is None:
            news_sources = []
        
        cache_key = f"{ticker}_{period}_{'_'.join(subreddits)}"
        if cache_key in self.cache:
            print(f"Using cached sentiment data for {cache_key}")
            return self.cache[cache_key]
        
        days = int(period.replace("d", ""))
        start_time = datetime.now(timezone.utc) - timedelta(days=days)
        
        data = []

    
        # reddit
        # 1. Reddit with ticker search
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                print(f"Searching Reddit r/{subreddit_name} for {ticker}")
                for submission in subreddit.search(f"{ticker}", limit=100, time_filter="month"):
                    if submission.created_utc < start_time.timestamp():
                        continue
                    text = submission.title + " " + (submission.selftext or "")
                    if not re.search(r'\b' + re.escape(ticker), text, re.IGNORECASE):
                        continue
                    print(f"Reddit r/{subreddit_name} post: {text[:50]}...")
                    data.append({
                        "timestamp": datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
                        "text": text,
                        "source": f"reddit_{subreddit_name}",
                        "ticker": ticker
                    })
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list()[:20]:
                        if comment.created_utc < start_time.timestamp():
                            continue
                        if not re.search(r'\b' + re.escape(ticker) + r'\b.*(stock|price|earnings|invest|apple)', comment.body, re.IGNORECASE):
                            continue
                        print(f"Reddit r/{subreddit_name} comment: {comment.body[:50]}...")
                        data.append({
                            "timestamp": datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
                            "text": comment.body,
                            "source": f"reddit_{subreddit_name}",
                            "ticker": ticker
                        })
                print(f"Reddit r/{subreddit_name} returned {len([d for d in data if d['source'] == f'reddit_{subreddit_name}'])} items")
            except Exception as e:
                print(f"Error fetching from Reddit r/{subreddit_name}: {str(e)}")
        
        '''
        # 2. Reddit with multiple methods
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                print(f"Searching Reddit r/{subreddit_name} for {ticker}")

                total_added = 0

                # Use different methods to maximize coverage
                for method in [subreddit.search, subreddit.top, subreddit.new, subreddit.hot]:
                    if method == subreddit.search:
                        submissions = method(f"{ticker} OR {ticker_to_company(ticker)}", limit=500, time_filter="all")
                    else:
                        submissions = method(limit=300)  # Adjust as needed

                    for submission in submissions:
                        if submission.created_utc < start_time.timestamp():
                            continue

                        text = f"{submission.title} {submission.selftext or ''}"
                        if not re.search(rf"\b{re.escape(ticker)}\b", text, re.IGNORECASE):
                            continue

                        data.append({
                            "timestamp": datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
                            "text": text.strip(),
                            "source": f"reddit_{subreddit_name}",
                            "ticker": ticker
                        })
                        total_added += 1

                print(f"Reddit r/{subreddit_name} returned {total_added} items")

            except Exception as e:
                print(f"Error fetching from r/{subreddit_name}: {e}")

        
        '''
        
        # NewsAPI
        try:
            news_query = ticker_to_company(ticker)
            params = {
                "q": news_query,
                "apiKey": self.newsapi_key,
                "language": "en",
                "from": start_time.strftime("%Y-%m-%d"),
                "sortBy": "relevancy"
            }
            if news_sources:
                params["sources"] = ",".join(news_sources)
            print(f"Searching NewsAPI with query: {news_query}")
            response = requests.get(self.newsapi_url, params=params)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            print(f"NewsAPI returned {len(articles)} articles for {news_query}")
            for article in articles[:50]:
                try:
                    published_at_str = article.get("publishedAt")
                    if not published_at_str:
                        continue
                    try:
                        published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
                    if published_at < start_time:
                        continue
                    title = article.get("title", "")
                    text = title 
                    if not text:
                        continue
                    print(f"NewsAPI article added: {text[:50]}...")
                    data.append({
                        "timestamp": published_at,
                        "text": text,
                        "source": "news",
                        "ticker": ticker
                    })
                except Exception as e:
                    print(f"NewsAPI article skipped: error processing {str(e)}")
        except Exception as e:
            print(f"Error fetching from NewsAPI: {str(e)}")
        
        df = pd.DataFrame(data)
        if df.empty:
            print(f"No sentiment data for {ticker} in {period}")
            return df
        
        self.cache[cache_key] = df
        return df

def ticker_to_company(ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).info
        name = info.get("shortName") or info.get("longName")
        if name:
            return name
    except Exception as e:
        print(f"Errore ottenendo nome azienda per {ticker}: {e}")
    return ticker

if __name__ == "__main__":
    fetcher = SentimentFetcher()
    df = fetcher.fetch_sentiment_data(
        ticker="AAPL",
        period="30d",
        subreddits=["wallstreetbets", "stocks", "investing"],
        news_sources=[]
    )
    print(df)
