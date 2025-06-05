from flask import Flask, render_template, request
from data.price_fetcher import PriceFetcher
from data.sentiment_fetcher import SentimentFetcher
from data.sentiment_cleaner import SentimentCleaner
from sentiment.sentiment_analyzer import SentimentAnalyzer
from indicators.indicator_fetcher import TechnicalIndicators
from strategy.strategy_computation import HybridStrategy
from evaluation.report_generator import GenerateReport

app = Flask(__name__)

# Aggiungiamo una route separata per l'analisi
@app.route('/analyze', methods=['POST'])
def analyze():
    ticker = request.form['ticker'].strip().upper()
    rsi_mode = request.form.get('rsi_mode', 'standard')
    
    try:
        # Inizializzazione moduli
        price_fetcher = PriceFetcher()
        sentiment_fetcher = SentimentFetcher()
        sentiment_cleaner = SentimentCleaner()
        sentiment_analyzer = SentimentAnalyzer()
        indicators_computation = TechnicalIndicators(ticker)
        report_generator = GenerateReport()

        # 1. Estrazione dati
        price_df = price_fetcher.fetch_price_data(ticker, period="30d")
        sentiment_df = sentiment_fetcher.fetch_sentiment_data(ticker, period="7d")

        # 2. Pulizia e analisi sentiment
        cleaned_df = sentiment_cleaner.clean_sentiment_data(sentiment_df)
        analyzed_df, sentiment_score = sentiment_analyzer.analyze_sentiment(cleaned_df)

        # 3. Calcolo indicatori tecnici
        rsi, adx, pe_ratio = indicators_computation.compute_indicators()
        print(f"RSI: {rsi}, ADX: {adx}, P/E Ratio: {pe_ratio}")

        # 4. Calcolo segnale strategico
        strategy = HybridStrategy()
        final_signal, confidence, total_score, explanation = strategy.generate_trading_signal(rsi, adx, pe_ratio, sentiment_score, rsi_mode)

        # Format sentiment_score for display
        sentiment_score = f"{sentiment_score:.2f}"

        # 5. report
        report = report_generator.generate_report(ticker, sentiment_score, final_signal, confidence, explanation)
        
        return render_template("index.html", 
                            ticker=ticker,
                            sentiment_score=sentiment_score,
                            final_signal=final_signal,
                            confidence=confidence,
                            error=None,
                            rsi_mode=rsi_mode,
                            report=report)

    except Exception as e:
        return render_template("index.html", 
                            ticker=ticker,
                            sentiment_score=None,
                            final_signal=None,
                            confidence=None,
                            error="No data retrieved. This may happen if the stock doesn't have enough historical data or indicators available.",
                            rsi_mode=rsi_mode,
                            report=None)

@app.route('/', methods=['GET'])
def home():
    # Pagina iniziale pulita senza risultati
    return render_template("index.html", 
                         ticker=None,
                         sentiment_score=None,
                         final_signal=None,
                         confidence=None,
                         error=None,
                         rsi_mode='standard',
                         report=None)

if __name__ == '__main__':
    app.run(debug=True)