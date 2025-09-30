
# Stock Alert Bot (Twitter)

## Overview
The **Stock Alert Bot** is a Python-based tool that monitors stock and crypto tickers, analyzes price movements using technical indicators, and automatically posts alerts to Twitter when trading signals occur. This bot is ideal for traders or enthusiasts who want automated alerts for overbought/oversold conditions and trend reversals.

---

## Features (MVP)

- **Monitor multiple tickers**: Supports US and Indian stocks, ETFs, and indices.  
- **Technical Indicators**:
  - **RSI (Relative Strength Index)**: Detects overbought and oversold conditions.
  - **MACD (Moving Average Convergence Divergence)**: Detects trend reversals and crossovers.  
- **Automated Twitter alerts**: Posts a tweet when signals are detected.  
- **Batch processing**: Fetches ticker data in configurable batches.  
- **Delisted ticker handling**: Automatically removes tickers with missing or delisted data.  
- **Resilient loop**: Runs continuously, handles errors, retries on failures.  

---

## Technical Explanation

### 1. Data Fetching
The bot uses [`yfinance`](https://pypi.org/project/yfinance/) to fetch historical OHLC (Open, High, Low, Close) price data for tickers. Example:

```python
df = yf.download(tickers='AAPL', period='1mo', interval='1h', auto_adjust=True)
````

* **Period**: How far back to fetch data (e.g., 1 month).
* **Interval**: The frequency of data points (e.g., hourly).
* **auto_adjust=True**: Adjusts for splits and dividends.

Tickers that return empty data are assumed to be delisted and removed from monitoring.

---

### 2. RSI Calculation

The **Relative Strength Index (RSI)** is a momentum oscillator that measures the speed and change of price movements.

* Formula:

[
RSI = 100 - \frac{100}{1 + RS}, \quad RS = \frac{\text{Average Gain}}{\text{Average Loss}}
]

* **Oversold condition**: RSI ≤ 30 → Potential buy signal.
* **Overbought condition**: RSI ≥ 70 → Potential sell signal.

Implemented via the `compute_rsi` function in `indicators.py`.

---

### 3. MACD Calculation

The **MACD (Moving Average Convergence Divergence)** detects trend changes. It uses two EMAs (Exponential Moving Averages):

* **MACD Line**: 12-period EMA − 26-period EMA
* **Signal Line**: 9-period EMA of MACD line
* **Crossover**:

  * Bullish: MACD crosses above Signal → Buy signal
  * Bearish: MACD crosses below Signal → Sell signal

Implemented using `compute_macd(df)` and `detect_macd_cross(df)` functions.

---

### 4. Alert Logic

* For each ticker, the bot computes RSI and MACD.
* Generates messages if:

  * RSI indicates overbought/oversold.
  * MACD indicates bullish/bearish crossover.
* Keeps track of previously sent alerts to avoid duplicate tweets.
* Posts alerts using Tweepy with Twitter v2 API.

Example Tweet:

```
$AAPL — 2025-09-30 15:30 IST
🔔 RSI = 28.7 (Oversold ≤ 30) → Possible Buy
📈 MACD crossover detected: BULLISH
```

---

### 5. Configuration

All configurable parameters are in `config.py`:

```python
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'RELIANCE.NS']  # List of tickers
YFINANCE_PERIOD = '1mo'
YFINANCE_INTERVAL = '1h'
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
CHECK_INTERVAL_SECONDS = 300  # Loop interval
BATCH_SIZE = 50               # Fetch 50 tickers per batch
TWEET_DELAY_SECONDS = 5       # Delay between tweets

# Twitter API credentials
TWITTER_API_KEY = 'your_api_key'
TWITTER_API_SECRET = 'your_api_secret'
TWITTER_ACCESS_TOKEN = 'your_access_token'
TWITTER_ACCESS_TOKEN_SECRET = 'your_access_token_secret'
TWITTER_BEARER_TOKEN = 'your_bearer_token'
```

---
=======
# stock-alert-bot
Python bot that monitors stocks and ETFs, computes RSI &amp; MACD signals, and posts alerts to Twitter in real-time. Built for quick alerts on overbought/oversold conditions and MACD crossovers. Configurable via a config.py file without exposing API keys.

