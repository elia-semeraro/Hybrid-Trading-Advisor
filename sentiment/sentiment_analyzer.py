import pandas as pd
from openai import OpenAI
import re
import os
import numpy as np
import yaml

class SentimentAnalyzer:
    """Analyzes sentiment using OpenAI's GPT model."""

    def __init__(self, config_path: str = None):
        """Initialize the OpenAI API client with settings from config/settings.yaml."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "settings.yaml")
        
        config_path = os.path.abspath(config_path)

        with open(config_path, 'r') as file:
            settings = yaml.safe_load(file)

        os.environ["OPENAI_API_KEY"] = settings['openai']['api_key']
        self.client = OpenAI()
        self.model_name = settings['openai']['model_name']
        self.prompt_template = (
            "You are a helpful assistant. Rate the sentiment, based on a financial point of view, of the following text with respect to the stock ticker {ticker} "
            "between -100 for very negative and 100 for very positive, where 0 is neutral. "
            "Report only the number. "
            "The text to rate is: '{text}'"
        )

    def get_sentiment_score(self, text: str, ticker: str, num_trials: int = 1) -> float:
        """Get the average sentiment score using OpenAI API."""
        scores = []
        prompt = self.prompt_template.format(ticker=ticker, text=text)

        for _ in range(num_trials):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a sentiment analysis expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    max_tokens=10,
                )
                reply = response.choices[0].message.content
                match = re.search(r'-?\d+', reply)
                if match:
                    score = int(match.group())
                    score = max(min(score, 100), -100)
                    scores.append(score)
                else:
                    scores.append(0.0)
            except Exception as e:
                print(f"Error during OpenAI API call: {e}")
                scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0

    def analyze_sentiment(self, df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
        """Analyze sentiment for each text and compute a weighted overall score."""
        if df.empty or 'cleaned_text' not in df.columns or 'source' not in df.columns or 'ticker' not in df.columns:
            print("Warning: Empty DataFrame or missing required columns.")
            return df, 0.0

        df['sentiment_score'] = df.apply(
            lambda row: self.get_sentiment_score(row['cleaned_text'], row['ticker']),
            axis=1
        )

        source_means = {}
        for source_type in ['reddit', 'news']:
            if source_type == 'reddit':
                mask = df['source'].str.startswith('reddit_')
            else:
                mask = df['source'] == source_type
            if mask.any():
                source_means[source_type] = df[mask]['sentiment_score'].mean()
            else:
                source_means[source_type] = None

        weights = {'news': 0.7, 'reddit': 0.3}
        total_weight = 0.0
        weighted_sum = 0.0

        for source, weight in weights.items():
            if source_means[source] is not None:
                weighted_sum += source_means[source] * weight
                total_weight += weight

        overall_score = (weighted_sum / total_weight * sum(weights.values())) if total_weight > 0 else 0.0
        overall_score = max(min(overall_score, 100), -100)

        print("Source means:", {k: v for k, v in source_means.items() if v is not None})
        print(f"Overall sentiment score: {overall_score:.2f}")

        return df, overall_score

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    sample_data = pd.DataFrame({
        'timestamp': [pd.Timestamp('2025-04-25 10:00:00+00:00')] * 3,
        'text': [
            "Apple Q2 earnings beat expectations! 🚀 $AAPL up 10%",
            "Apple unveils new iPhone 16 for $999... 😊",
            "AAPL stock plummets after lawsuit news 😞"
        ],
        'cleaned_text': [
            "Apple Q2 earnings beat expectations! 🚀 $AAPL up 10%",
            "Apple unveils new iPhone 16 for $999... 😊",
            "AAPL stock plummets after lawsuit news 😞"
        ],
        'source': ['reddit_wallstreetbets', 'news', 'news'],
        'ticker': ['AAPL', 'AAPL', 'AAPL']
    })
    result_df, overall_score = analyzer.analyze_sentiment(sample_data)
    print(result_df)
    print(f"Final sentiment score: {overall_score:.2f}")
