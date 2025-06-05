import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from datetime import datetime, timedelta
from config.backtest_config import BacktestConfig
from data.price_fetcher import PriceFetcher  # Assumed to return OHLC DataFrame

class TechnicalIndicators:
    """Computes technical indicators (RSI, ADX, P/E ratio) for a stock."""

    def __init__(self, ticker: str, price_fetcher: Optional[PriceFetcher] = None):
        self.ticker = ticker.upper()
        self.price_fetcher = price_fetcher or PriceFetcher()
        self.stock = yf.Ticker(ticker)

    def fetch_price_data(self, period = '6mo', interval ='1d') -> pd.DataFrame:
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
        if len(price_series) < period:
            print(f"Warning: Insufficient data for RSI calculation (need {period} periods, got {len(price_series)})")
            return pd.Series(index=price_series.index, dtype=float)

        try:
            delta = price_series.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=period, min_periods=period).mean()
            avg_loss = loss.rolling(window=period, min_periods=period).mean()

            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            return rsi.rename('RSI')
        except Exception as e:
            print(f"Error computing RSI: {e}")
            return pd.Series(index=price_series.index, dtype=float)

    def compute_adx(self, data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
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

            plus_dm = pd.Series(np.where((high.diff() > low.diff()) & (high.diff() > 0), high.diff(), 0.0), index=data.index)
            minus_dm = pd.Series(np.where((low.diff() > high.diff()) & (low.diff() > 0), low.diff(), 0.0), index=data.index)

            tr = pd.DataFrame({
                'tr1': high - low,
                'tr2': abs(high - close.shift()),
                'tr3': abs(low - close.shift())
            }).max(axis=1)
            atr = tr.rolling(window=period, min_periods=period).mean()

            plus_di = 100 * plus_dm.ewm(span=period, adjust=False, min_periods=period).mean() / atr
            minus_di = 100 * minus_dm.ewm(span=period, adjust=False, min_periods=period).mean() / atr

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
        try:
            info = self.stock.info
            pe_ratio = info.get('trailingPE')
            if pe_ratio is None:
                print(f"Warning: P/E ratio not available for {self.ticker}")
            return pe_ratio
        except Exception as e:
            print(f"Error fetching P/E ratio for {self.ticker}: {e}")
            return None

    def compute_indicators_on_date_range(self, start_date, end_date, interval: str = '1d', rsi_period: int = 14, adx_period: int = 14) -> pd.DataFrame:
        results = []
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        full_data = self.fetch_price_data(period='1y', interval=interval)
        if full_data.empty:
            print("No price data available.")
            return pd.DataFrame()

        # Rimuovi il timezone dall'indice
        full_data.index = full_data.index.tz_localize(None)


        for single_date in pd.date_range(start=start_dt, end=end_dt):
            end_window = single_date
            start_window = end_window - timedelta(days=40)


            print(f"→ {single_date.date()} | Window: {start_window.date()} to {end_window.date()}")


            window_data = full_data[(full_data.index >= start_window) & (full_data.index <= end_window)]
            if len(window_data) < 14:
                continue

            rsi_series = self.compute_rsi(window_data['Close'], rsi_period).dropna()
            adx_df = self.compute_adx(window_data, adx_period).dropna(subset=['ADX'])


            if rsi_series.empty:
                print(f"  - RSI is empty after dropna()")
            if adx_df['ADX'].empty:
                print(f"  - ADX is empty after dropna()")

            try:
                rsi_value = rsi_series.iloc[-1]
                adx_value = adx_df['ADX'].iloc[-1]

                results.append({
                    'Date': single_date,
                    'RSI': rsi_value,
                    'ADX': adx_value
                })
                print(f"\n Appended indicators: RSI={rsi_value:.2f}, ADX={adx_value:.2f}")

            except Exception as e:
                print(f"   Skipping due to error: {e}")

        df = pd.DataFrame(results)


            

        if df.empty:
            print("\nFinal result: No indicators computed.\n")
            return df

        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        print(f"\nFinal DataFrame with {len(df)} rows computed.")
        return df



        if df.empty:
            print("\nFinal result: No indicators computed.\n")
            return df

        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        print(f"\n Final DataFrame with {len(df)} rows computed.")
        return df
 
# === MAIN EXECUTION BLOCK ===

if __name__ == "__main__":
    try:
        # Importa configurazione
        config = BacktestConfig()
        ticker = config.ticker
        start_date = config.start_date
        end_date = config.end_date

        # Inizializza e calcola gli indicatori
        indicators = TechnicalIndicators(ticker)
        df = indicators.compute_indicators_on_date_range(start_date=start_date, end_date=end_date)

        if df.empty:
            print("No indicators could be computed.")
        else:
            print(df)

    except Exception as e:
        print(f"Error in main: {e}")
