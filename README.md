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
  username: "YOUR_REDDIT_USERNAME" 
  password: "YOUR_REDDIT_PASSWORD"
  user_agent: "YOUR_REDDIT_USER_AGENT"

newsapi:
  api_key: "YOUR_NEWSAPI_KEY"

openai:
  api_key: "YOUR_OPENAI_API_KEY"
  model_name: "MODEL_TO_USE"
```

#### Follow these steps to get what you need.

#### Reddit API credentials

1.	Go to https: https://www.reddit.com/prefs/apps.
2.	Scroll to "Developed Applications", (for new accounts click on "Are you a developer? Create an app").
3.	Click on “Create App” or “Create Another App”.
4.	Fill out the form:
- Name: (e.g. HybridTradingAdvisor)
- App type: Select "script"
- Redirect URI: Use http://localhost:8080 (required but not used in scripts).
- Description: Optional
5.	After creation, you'll see:
- client_id: displayed under the app name.
- client_secret: visible once the app is created.
- username: your Reddit account.
- password: your Reddit password.
- user_agent: any string that identifies your app (recommended format: "YourAppName/Version by YourRedditUsername").

#### News API credentials
1.	Go to https: https://newsapi.org.
2.	Sign up for a free account.
3.	Once logged in, navigate to “API” or your Dashboard.
4.	Your API key will be available there — copy it.

#### OPENAI API credentials
1.	Go to https: https://platform.openai.com/signup and create an account (or login).
2.	Navigate to https://platform.openai.com/account/api-keys.
3.	Click "Create new secret key".
4.	Copy and store the key securely. You will not see it again.

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
├── run_backtest.py                    # Script for running historical backtests
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

## How to Run a Backtest

1. Ensure you have filled in the `config/backtest_config.py` file with the settings required.

3. Run Backtest_1.py:

```bash
python run_backtest.py
```
4. Wait 5 to 30 minutes, depending on computational effort required and view the total return of advisor's positions.

## Future Improvements

- Integration of stochastic oscillator and Bollinger Bands.
- Limit orders and transaction cost simulation.
- Dynamic weighting.
- Real-time data processing infrastructure.
- Anomaly detection for sentiment spikes.

## License

This project is for educational and non-commercial use only.  
All rights to external libraries and APIs remain with their respective owners.
