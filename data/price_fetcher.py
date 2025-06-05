import yfinance as yf
import pandas as pd

class PriceFetcher:
    """Fetches price data from Yahoo Finance."""

    def fetch_price_data(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Fetch historical price data for a given ticker.

        Args:
            ticker (str): Stock ticker (e.g., "AAPL").
            period (str): Period (e.g., "1y", "6mo").
            interval (str): Data interval (e.g., "1d", "1h").

        Returns:
            pd.DataFrame: OHLCV data with datetime index, or empty DataFrame if failed.
        """
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)

        if df.empty:
            print(f"No price data for {ticker}")
            return pd.DataFrame()

        print("Preview of data fetched:")
        return df[['Open', 'High', 'Low', 'Close', 'Volume']]


    #volendo il fetch_latest_price si può togliere. l'unica comodità è che genera l'ultimo prezzo disponibile senza prendere tutta la serie storica, verificheremo se può essere utile o meno
    def fetch_latest_price(self, ticker: str) -> dict:
        """
        Fetch the latest price data.

        Args:
            ticker (str): Stock ticker (e.g., "AAPL").

        Returns:
            dict: Latest price data, or empty dict if failed.
        """
        stock = yf.Ticker(ticker)
        df = stock.history(period="1d", interval="1m")

        if df.empty:
            print(f"No latest price data for {ticker}")
            return {}

        latest = df.iloc[-1]
        return {
            "ticker": ticker,
            "timestamp": df.index[-1],
            "close": latest["Close"],
            "volume": latest["Volume"]
        }

if __name__ == "__main__":
    # Example usage
    fetcher = PriceFetcher()
    df = fetcher.fetch_price_data("AAPL", period="1y", interval="1d")
    print(df.head())
    latest = fetcher.fetch_latest_price("AAPL")
    print(latest)