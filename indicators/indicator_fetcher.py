import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple

from data.price_fetcher import PriceFetcher  # Assumed to return OHLC DataFrame

class TechnicalIndicators:
    """Computes technical indicators (RSI, ADX, P/E ratio) for a stock."""

    def __init__(self, ticker: str, price_fetcher: Optional[PriceFetcher] = None):
        """
        Initialize with ticker and optional PriceFetcher.
        
        Args:
            ticker (str): Stock ticker (e.g., 'AAPL').
            price_fetcher (PriceFetcher, optional): Instance of PriceFetcher. Defaults to None (creates new).
        """
        self.ticker = ticker.upper()
        self.price_fetcher = price_fetcher or PriceFetcher()
        self.stock = yf.Ticker(ticker)

    def fetch_price_data(self, period: str = '6mo', interval: str = '1d') -> pd.DataFrame:
        """
        Fetch price data using PriceFetcher.
        
        Args:
            period (str): Data period (e.g., '6mo', '1y'). Default: '6mo'.
            interval (str): Data interval (e.g., '1d', '1h'). Default: '1d'.
        
        Returns:
            pd.DataFrame: OHLC data with columns ['Open', 'High', 'Low', 'Close', 'Volume'].
        """
        try:
            df = self.price_fetcher.fetch_price_data(self.ticker, period=period, interval=interval)
            required_columns = {'Open', 'High', 'Low', 'Close'}
            if df.empty or not required_columns.issubset(df.columns):
                raise ValueError(f"Insufficient data for {self.ticker}. Required columns: {required_columns}")
            return df
        except Exception as e:
            print(f"Error fetching price data for {self.ticker}: {e}")
            return pd.DataFrame()

    def compute_rsi(self, price_series: pd.Series, period: int = 14) -> pd.Series:
        """
        Compute Relative Strength Index (RSI).
        
        Args:
            price_series (pd.Series): Series of closing prices.
            period (int): Lookback period. Default: 14.
        
        Returns:
            pd.Series: RSI values.
        """
        if len(price_series) < period:
            print(f"Warning: Insufficient data for RSI calculation (need {period} periods, got {len(price_series)})")
            return pd.Series(index=price_series.index, dtype=float)

        try:
            delta = price_series.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=period, min_periods=period).mean()
            avg_loss = loss.rolling(window=period, min_periods=period).mean()

            # Avoid division by zero
            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            return rsi.rename('RSI')
        except Exception as e:
            print(f"Error computing RSI: {e}")
            return pd.Series(index=price_series.index, dtype=float)

    def compute_adx(self, data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Compute Average Directional Index (ADX) and DI indicators.
        
        Args:
            data (pd.DataFrame): DataFrame with ['High', 'Low', 'Close'] columns.
            period (int): Lookback period. Default: 14.
        
        Returns:
            pd.DataFrame: Columns ['PlusDI', 'MinusDI', 'ADX'].
        """
        required_columns = {'High', 'Low', 'Close'}
        if not required_columns.issubset(data.columns):
            print(f"Error: Missing required columns for ADX: {required_columns - set(data.columns)}")
            return pd.DataFrame(index=data.index)

        if len(data) < period:
            print(f"Warning: Insufficient data for ADX calculation (need {period} periods, got {len(data)})")
            return pd.DataFrame(index=data.index, columns=['PlusDI', 'MinusDI', 'ADX'])

        try:
            high = data['High']
            low = data['Low']
            close = data['Close']

            # Directional Movement
            plus_dm = high.diff()
            minus_dm = low.diff()
            
            plus_dm = pd.Series(np.where((high.diff() > low.diff()) & (high.diff() > 0), high.diff(), 0.0), index=data.index)
            minus_dm = pd.Series(np.where((low.diff() > high.diff()) & (low.diff() > 0), low.diff(), 0.0), index=data.index)

            # True Range
            tr = pd.DataFrame({
                'tr1': high - low,
                'tr2': abs(high - close.shift()),
                'tr3': abs(low - close.shift())
            }).max(axis=1)
            atr = tr.rolling(window=period, min_periods=period).mean()

            # Smoothed Directional Indicators
            plus_di = 100 * pd.Series(plus_dm).ewm(span=period, adjust=False, min_periods=period).mean() / atr
            minus_di = 100 * pd.Series(minus_dm).ewm(span=period, adjust=False, min_periods=period).mean() / atr

            # Directional Index (DX) and ADX
            dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
            adx = dx.ewm(span=period, adjust=False, min_periods=period).mean()

            return pd.DataFrame({
                'PlusDI': plus_di,
                'MinusDI': minus_di,
                'ADX': adx
            }, index=data.index)
        except Exception as e:
            print(f"Error computing ADX: {e}")
            return pd.DataFrame(index=data.index, columns=['PlusDI', 'MinusDI', 'ADX'])

    def get_pe_ratio(self) -> Optional[float]:
        """
        Get the trailing P/E ratio for the ticker.
        
        Returns:
            Optional[float]: P/E ratio or None if unavailable.
        """
        try:
            info = self.stock.info
            pe_ratio = info.get('trailingPE')
            if pe_ratio is None:
                print(f"Warning: P/E ratio not available for {self.ticker}")
            return pe_ratio
        except Exception as e:
            print(f"Error fetching P/E ratio for {self.ticker}: {e}")
            return None

    def compute_indicators(self, period: str = '6mo', interval: str = '1d',
                        rsi_period: int = 14, adx_period: int = 14) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Compute RSI, ADX, and P/E ratio for the latest available day.

        Args:
            period (str): Data period. Default: '6mo'.
            interval (str): Data interval. Default: '1d'.
            rsi_period (int): RSI lookback period. Default: 14.
            adx_period (int): ADX lookback period. Default: 14.

        Returns:
            Tuple[RSI (float), ADX (float), P/E ratio (float)]: Latest values, or None if unavailable.
        """
        df = self.fetch_price_data(period, interval)
        if df.empty:
            return None, None, None

        rsi_series = self.compute_rsi(df['Close'], rsi_period)
        adx_df = self.compute_adx(df, adx_period)
        pe_ratio = self.get_pe_ratio()

        # Trova l'ultima data con dati validi (dropna su entrambe le serie)
        indicators_df = pd.DataFrame({
            'RSI': rsi_series,
            'ADX': adx_df['ADX']
        }).dropna()

        if indicators_df.empty:
            return None, None, pe_ratio

        latest_row = indicators_df.iloc[-1]
        return latest_row['RSI'], latest_row['ADX'], pe_ratio



def main():
    """Example usage."""
    try:
        indicators = TechnicalIndicators('META')
        rsi, adx, pe_ratio = indicators.compute_indicators(period='6mo', interval='1d')

        if rsi is not None and adx is not None:
            print(f"RSI: {rsi:.6f}")
            print(f"ADX: {adx:.6f}")
        else:
            print("RSI or ADX could not be computed.")
        
        if pe_ratio is not None:
            print(f"P/E Ratio: {pe_ratio:.6f}")
        else:
            print("P/E Ratio: N/A")

    except Exception as e:
        print(f"Error in main: {e}")




if __name__ == "__main__":
    main()