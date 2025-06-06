import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone
from data.price_fetcher import PriceFetcher
from data.backtest_sentiment_fetcher import SentimentFetcher
from data.sentiment_cleaner import SentimentCleaner
from strategy.strategy_computation import HybridStrategy
from sentiment.sentiment_analyzer import SentimentAnalyzer
from indicators.backtest_indicator_fetcher import TechnicalIndicators
from config.backtest_config import BacktestConfig

# === Inizializza configurazione ===
config = BacktestConfig()
ticker = config.ticker
start_date = config.start_date
end_date = config.end_date
initial_cash = config.initial_cash

# === Inizializza moduli ===
price_fetcher = PriceFetcher()
strategy = HybridStrategy()
fetcher = SentimentFetcher()
cleaner = SentimentCleaner()
analyzer = SentimentAnalyzer()
indicators = TechnicalIndicators(ticker)

# Calcolo anticipato degli indicatori per tutte le date
indicator_df = indicators.compute_indicators_on_date_range(start_date, end_date)


# === Ottieni dati storici per RSI/ADX + segnali
full_price_df = price_fetcher.fetch_price_data(ticker, period="3mo").dropna()  # o 30d se vuoi stare largo

# === Seleziona l'intervallo di giorni per cui generare segnali
full_price_df.index = full_price_df.index.tz_localize(None)

# Filtra le date esattamente nell'intervallo
price_df = full_price_df.loc[start_date:end_date].copy()
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)


#Printo per accertarmi che le date siano corrette
print(f"Date effettivamente usate ({len(price_df)} giorni):")
print(price_df.index.tolist())


price_df.loc[:,'Final_Signal'] = None
price_df.loc[:,'SentimentScore'] = None
price_df.loc[:,'RSI'] = None
price_df.loc[:,'ADX'] = None
price_df.loc[:,'PE_ratio'] = None
price_df.loc[:,'rsi_mode'] = None

# === Backtest ===
cash = initial_cash
position = 0
short_position = 0
holding = False
holding_short = False
portfolio_value = []

records = []  # lista per raccogliere righe da salvare in Excel
position_log = []  # log di aperture/chiusure
open_position_date = None
open_position_type = None
opening_price = None  # prezzo di apertura della posizione

for date, row in price_df.iterrows():
    try:
        # Sentiment
        sentiment_window_start = date - pd.Timedelta(config.period)
        sentiment_window_end = date

        sentiment_df = fetcher.fetch_sentiment_data(ticker, sentiment_window_start, sentiment_window_end)
        cleaned_df = cleaner.clean_sentiment_data(sentiment_df)
        analyzed_df, sentiment_score = analyzer.analyze_sentiment(cleaned_df)


        try:
            rsi = float(indicator_df.loc[date, 'RSI'])
            adx = float(indicator_df.loc[date, 'ADX'])
        except KeyError:
            print(f"Indicatori non trovati per la data {date}, passo al giorno successivo.")
            portfolio_value.append(cash + position * row['Close'])
            continue

            pe_ratio = 20  # Inserisci qui il P/E ratio per il giorno


        volatility = 0.01  # Placeholder: puoi calcolare una vera volatilità qui
        if volatility < 0.005:
            rsi_mode = "aggressive"
        elif volatility <= 0.03:
            rsi_mode = "standard"
        else:
            rsi_mode = "conservative"

        pe_ratio = 20  # Placeholder fisso, oppure qui puoi calcolarlo se hai i dati  


        final_signal, confidence_level, total_score, explanation = strategy.generate_trading_signal(rsi, adx, pe_ratio, sentiment_score, rsi_mode)
        

    
        price_df.at[date, 'Signal'] = final_signal
        price_df.at[date, 'SentimentScore'] = sentiment_score
        price_df.at[date, 'RSI'] = rsi
        price_df.at[date, 'ADX'] = adx
        price_df.at[date, 'PE_ratio'] = pe_ratio
        price_df.at[date, 'rsi_mode'] = rsi_mode

        price = row['Close']

        # === Tracciamento apertura e chiusura posizioni ===
        if final_signal in ["Buy"] and not holding:
            open_position_date = date
            open_position_type = "long"
            position_log.append(f"Apertura posizione long il {date.date()}.")
            holding = True
            opening_price = price

        elif final_signal in ["Sell"] and not holding_short:
            open_position_date = date
            open_position_type = "short"
            position_log.append(f"Apertura posizione short il {date.date()}.")
            holding_short = True
            opening_price = price

        # Chiusura long se il segnale è di natura opposta o neutra
        elif holding and final_signal in ["Hold","Sell"]:
            position_log.append(f"Chiusura posizione long il {date.date()}.")
            open_position_date = None
            open_position_type = None
            holding = False
            position = 0
            openening_price = None

        # Chiusura short se il segnale è di natura opposta o neutra
        elif holding_short and final_signal in ["Hold", "Buy"]:
            position_log.append(f"Chiusura posizione short il {date.date()}.")
            open_position_date = None
            open_position_type = None
            holding_short = False
            short_position = 0
            opening_price = None


        # Salva i dati in una lista per CSV
        records.append({
            'Date': date,
            'Close': price,
            'SentimentScore': sentiment_score,
            'RSI': rsi,
            'ADX': adx,
            'PE_ratio': pe_ratio,
            'RSI_mode': rsi_mode,
            'Signal': final_signal,
            'Confidence_Level': confidence_level,
            'Total_Score': total_score
             })

        print(f"{date},{price:.2f},{sentiment_score:.1f},{rsi},{adx},{final_signal.lower()}, {confidence_level}, {explanation}")

    except Exception as e:
        print(f"Errore per il giorno {date}: {e}")


# === Controllo finale su posizione ancora aperta ===
if open_position_date:
    position_log.append(f" Posizione {open_position_type} ancora aperta alla fine del periodo (ultimo giorno: {price_df.index[-1].date()}).")

print("\n=== LOG STRATEGIA: Aperture/Chiusure ===")
for event in position_log:
    print(event)

# === Return Calculation ===
returns = []
open_type = None
open_date = None

for event in position_log:
    if "Apertura posizione" in event:
        open_type = "long" if "long" in event else "short"
        open_date = pd.to_datetime(event.split("il ")[1].strip())

    elif "Chiusura posizione" in event and open_type and open_date:
        close_date = pd.to_datetime(event.split("il ")[1].strip())
        open_price = price_df.loc[open_date, "Close"]
        close_price = price_df.loc[close_date, "Close"]

        if open_type == "long":
            ret = (close_price - open_price) / open_price
        else:
            ret = (open_price - close_price) / open_price
        returns.append(ret)
        open_type = None
        open_date = None

# === Final Portfolio Evaluation ===
if end_date not in price_df.index:
    end_date = price_df.index[price_df.index <= end_date][-1]
current_price = price_df.loc[end_date, "Close"]

if (holding or holding_short) and not returns:
    if opening_price is not None:
        quantity = initial_cash / opening_price
        if holding:
            final_cash = quantity * current_price
        else:
            final_cash = initial_cash + quantity * (opening_price - current_price)
        gain_pct = (final_cash - initial_cash) / initial_cash * 100
        status = "Opened but not closed"
    else:
        final_cash = initial_cash
        gain_pct = 0.0
        status = "Error: open_price missing"

elif returns:
    total_return = sum(returns)
    final_cash = initial_cash * (1 + total_return)
    gain_pct = total_return * 100
    status = "Opened and closed"

else:
    final_cash = initial_cash
    gain_pct = 0.0
    status = "No positions opened"

# === Print Summary ===
print("\n=== FINAL SUMMARY ===")
print(f"Status: {status}")
print(f"Final Portfolio Value: ${final_cash:,.2f}")
print(f"Total Gain/Loss: {gain_pct:.2f}%")

# === Save to CSV ===
output_df = pd.DataFrame(records)
output_df.to_csv("backtest_output.csv", index=False)
