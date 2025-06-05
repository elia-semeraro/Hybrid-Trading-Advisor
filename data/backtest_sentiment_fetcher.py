import praw
import requests
import pandas as pd
import yaml
import re
import os
from datetime import datetime, timedelta, timezone
import yfinance as yf 
from config.backtest_config import BacktestConfig

class SentimentFetcher:
    """Fetches sentiment data from Reddit and NewsAPI with in-memory caching."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "settings.yaml")
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        reddit_config = config['reddit']
        self.reddit = praw.Reddit(
            client_id=reddit_config['client_id'],
            client_secret=reddit_config['client_secret'],
            username=reddit_config['username'],
            password=reddit_config['password'],
            user_agent=reddit_config['user_agent']
        )

        self.newsapi_key = config['newsapi']['api_key']
        self.newsapi_url = "https://newsapi.org/v2/everything"
        self.cache = {}

    def fetch_sentiment_data(self, ticker: str, start_time, end_time, 
                             subreddits: list = None, 
                             news_sources: list = None) -> pd.DataFrame:
        if subreddits is None:
            subreddits = ["wallstreetbets", "stocks", "investing", "StockMarket", "finance"]
        if news_sources is None:
            news_sources = []

        data = []

        cache_key = f"{ticker}_{start_time.date()}_{end_time.date()}_{'_'.join(subreddits)}"
        if cache_key in self.cache:
            print(f"Using cached sentiment data for {cache_key}")
            return self.cache[cache_key]



        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                print(f"Searching Reddit r/{subreddit_name} for {ticker}")
                results_count = 0
                for submission in subreddit.search(f"{ticker}", limit=200, time_filter="all"):
                    created_at = datetime.fromtimestamp(submission.created_utc)
                    if not (start_time <= created_at < end_time):
                        continue
                    text = submission.title + " " + (submission.selftext or "")
                    if not re.search(r'\b' + re.escape(ticker), text, re.IGNORECASE):
                        continue
                    print(f"Reddit r/{subreddit_name} post: {text[:50]}...")
                    data.append({
                        "timestamp": created_at,
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


     #NewsAPI           
        try:
            news_query = ticker_to_company(ticker)
            params = {
                "q": news_query,
                "apiKey": self.newsapi_key,
                "language": "en",
                "from": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
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
                    published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ")
                    if not (start_time <= published_at < end_time):
                        continue
                    title = article.get("title", "")
                    if not title:
                        continue
                    print(f"NewsAPI article added: {title[:50]}...")
                    data.append({
                        "timestamp": published_at,
                        "text": title,
                        "source": "news",
                        "ticker": ticker
                    })
                except Exception as e:
                    print(f"NewsAPI article skipped: error processing {str(e)}")
        except Exception as e:
            print(f"Error fetching from NewsAPI: {str(e)}")

        df = pd.DataFrame(data)
        return df

def ticker_to_company(ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).info
        return info.get("shortName") or info.get("longName") or ticker
    except Exception as e:
        print(f"Errore ottenendo nome azienda per {ticker}: {e}")
        return ticker


if __name__ == "__main__":
    config = BacktestConfig()
    fetcher = SentimentFetcher()
    all_data = []

    current_date = config.start_date
    period_days = int(config.period.replace("d", ""))
    while current_date <= config.end_date:
        start_time = current_date - timedelta(days=period_days)
        end_time = current_date
        print(f"Fetching sentiment from {start_time.date()} to {end_time.date()} for ticker {config.ticker}")
        df = fetcher.fetch_sentiment_data(
            ticker=config.ticker,
            start_time=start_time,
            end_time=end_time,
            subreddits=["wallstreetbets", "stocks", "investing","StockMarket", "finance"],
            news_sources=[]
        )
        df["reference_date"] = current_date
        all_data.append(df)
        current_date += timedelta(days=1)

    final_df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
    print(final_df)