# Hybrid Trading Advisor

## Overview

The Hybrid Trading Advisor is a Python-based system that integrates **technical analysis** and **sentiment analysis** to generate trading signals. It leverages modular architecture and combines structured market data with unstructured sentiment data from sources such as Reddit and financial news APIs. The trading strategy is risk-aware, customizable by user profile (Conservative, Standard, Aggressive), and features a user-friendly web dashboard.

## Key Features

- Modular Python codebase for flexible development and maintenance.
- Sentiment analysis via LLMs using Reddit and financial news.
- Technical indicators: RSI and ADX.
- Optional confidence adjustment via P/E ratio.
- Flask-based web dashboard for user interaction.
- Output: Buy, Sell, or Hold signals with associated confidence scores.

## Requirements

### Python Version
- Python 3.9 or higher is recommended.

### Python Dependencies

Install the required packages using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

#### Third-party packages include:

- `flask`
- `matplotlib`
- `numpy`
- `openai`
- `pandas`
- `praw`
- `requests`
- `pyyaml`
- `yfinance`

> The Python standard library modules (e.g., `datetime`, `os`, `re`, `typing`) are included by default and do **not** need installation.

## Configuration

### API Keys

This project relies on third-party APIs for sentiment data and LLM-based scoring. **Users must insert their own API keys** in the configuration file before running the application.

1. Open the configuration file:
   ```
   config/settings.yaml
   ```

2. Insert your API credentials in the following format:

```yaml
reddit:
  client_id: "YOUR_REDDIT_CLIENT_ID"
  client_secret: "YOUR_REDDIT_CLIENT_SECRET"
  user_agent: "YOUR_REDDIT_USER_AGENT"

newsapi:
  api_key: "YOUR_NEWSAPI_KEY"

openai:
  api_key: "YOUR_OPENAI_API_KEY"
```

**Do not share your API keys publicly.** These are required to fetch sentiment data and to run LLM-based sentiment classification.

## How to Use

1. Clone or download this repository.

2. Ensure you have filled in the `config/settings.yaml` file with your API keys.

3. Run main.py:

```bash
python main.py
```

4. Open your browser and go to:  
   ```
   http://127.0.0.1:5000/
   ```

5. Enter the asset ticker and select a trading profile (Conservative, Standard, or Aggressive). Click **Analyze**.

6. View the result: Final signal, confidence level, sentiment scores, and explanation.

## Project Structure

```
hybrid_trading_advisor/
│
├── main.py                            # Entry point of the application for real-time operation
├── Backtest_1.py                      # Script for running historical backtests
├── requirements.txt                   # Python dependencies for the project
│
├── config/                            # Centralized configuration management
│   ├── backtest_config.py             # Configuration specific to backtesting
│   ├── settings.yaml                  # General application settings and parameters
│
├── data/                              # Modules for data acquisition and preprocessing
│   ├── price_fetcher.py               # Handles fetching historical and real-time price data
│   ├── sentiment_fetcher.py           # Retrieves raw sentiment data from various sources
│   ├── sentiment_cleaner.py           # Cleans and preprocesses raw sentiment data
│   ├── backtest_sentiment_fetcher.py  # Specific sentiment data fetching for backtesting
│
├── indicators/                        # Modules for technical indicator computation
│   ├── indicator_fetcher.py           # Computes technical indicators for real-time use
│   ├── backtest_indicator_fetcher.py  # Computes technical indicators for backtesting
│
├── sentiment/                         # Core sentiment analysis logic
│   ├── sentiment_analyzer.py          # Processes and scores sentiment data
│
├── strategy/                          # Trading strategy formulation logic
│   ├── strategy_computation.py        # Implements the hybrid signal generation logic
│
├── evaluation/                        # Performance evaluation and reporting
│   ├── report_generator.py            # Generates comprehensive performance reports
│
├── static/                            # Static web files
│   └── style.css                      # Custom CSS for web interface styling
│
├── templates/                         # HTML templates for the web interface
│   └── index.html                     # Main HTML file for the user interface
```

## Testing and Performance

The strategy was backtested on one month of historical data, with daily signal generation. It yielded:
- Average: 1.1 trades/day
- Average return: 1.34% over an average two weeks timespan
- Peak return days: 15.62% and 11.59%

Backtesting was constrained by data limits (e.g., NewsAPI free tier).

## Future Improvements

- Integration of stochastic oscillator and Bollinger Bands.
- Limit orders and transaction cost simulation.
- Dynamic weighting.
- Real-time data processing infrastructure.
- Anomaly detection for sentiment spikes.

## License

This project is for educational and non-commercial use only.  
All rights to external libraries and APIs remain with their respective owners.
