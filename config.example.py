#rename this to config.py with your api keys
# =======================
# Twitter API credentials
# =======================
TWITTER_API_KEY = ''
TWITTER_API_SECRET = ''
TWITTER_ACCESS_TOKEN = ''
TWITTER_ACCESS_TOKEN_SECRET = ''
TWITTER_BEARER_TOKEN = ""

# =======================
# All tickers (US + India + ETFs)
# =======================
TICKERS = [
    # Top US Large & Mid Caps
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'FB', 'TSLA', 'NVDA', 'JPM', 'V', 'JNJ',

    # Top Indian Large Caps
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'HINDUNILVR.NS', 

    # Popular ETFs / Indices
    'SPY', 'QQQ', 'DIA', 'IWM', 'NIFTYBEES.NS', 'BANKBEES.NS'
]


# =======================
# Yahoo Finance settings
# =======================
YFINANCE_PERIOD = '1mo'      # fetch last 1 month
YFINANCE_INTERVAL = '1h'     # 1-hour interval

# =======================
# Indicator thresholds
# =======================
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# =======================
# Bot Settings
# =======================
CHECK_INTERVAL_SECONDS = 300   # check every 5 minutes
BATCH_SIZE = 50                # fetch 50 tickers per batch
TWEET_DELAY_SECONDS = 5        # wait 5 seconds between tweets

# =======================
# Logging (optional)
# =======================
LOG_FILE = "bot.log"
