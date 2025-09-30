import os
import time
import logging
from datetime import datetime, timezone
import yfinance as yf
import pandas as pd
import tweepy
from indicators import compute_rsi, compute_macd, detect_macd_cross

# Try to import local config
try:
    import config as cfg
except ImportError:
    cfg = None

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Twitter credentials: prefer environment variables, fallback to config.py
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY") or (cfg.TWITTER_API_KEY if cfg else None)
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET") or (cfg.TWITTER_API_SECRET if cfg else None)
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN") or (cfg.TWITTER_ACCESS_TOKEN if cfg else None)
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET") or (cfg.TWITTER_ACCESS_TOKEN_SECRET if cfg else None)
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN") or (cfg.TWITTER_BEARER_TOKEN if cfg else None)

# Check keys
if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN]):
    logger.error("Twitter API keys are missing! Set them in config.py or environment variables.")
    exit(1)

# Twitter client
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

# Tickes and settings
tickers = cfg.TICKERS.copy() if cfg else []
RSI_OVERBOUGHT = getattr(cfg, "RSI_OVERBOUGHT", 70)
RSI_OVERSOLD = getattr(cfg, "RSI_OVERSOLD", 30)
CHECK_INTERVAL_SECONDS = getattr(cfg, "CHECK_INTERVAL_SECONDS", 300)
BATCH_SIZE = getattr(cfg, "BATCH_SIZE", 50)
YFINANCE_PERIOD = getattr(cfg, "YFINANCE_PERIOD", "1mo")
YFINANCE_INTERVAL = getattr(cfg, "YFINANCE_INTERVAL", "1h")
TWEET_DELAY_SECONDS = getattr(cfg, "TWEET_DELAY_SECONDS", 5)

last_alerts = {}

def fetch_data_batch(tickers_batch):
    """Fetch data for multiple tickers, remove delisted ones."""
    df_all = {}
    removed = []
    for ticker in tickers_batch:
        try:
            df = yf.download(
                tickers=ticker,
                period=YFINANCE_PERIOD,
                interval=YFINANCE_INTERVAL,
                progress=False,
                threads=False,
                auto_adjust=True
            )
            if df.empty:
                logger.warning(f"No data for ticker: {ticker}. Removing from list.")
                removed.append(ticker)
                continue
            df_all[ticker] = df
        except Exception as e:
            logger.error(f"Failed download: {ticker} -> {e}")
            removed.append(ticker)

    # Remove delisted tickers permanently
    for t in removed:
        if t in tickers:
            tickers.remove(t)
            logger.info(f"Removed delisted/missing ticker: {t}")
    return df_all

def analyze_ticker(ticker, df):
    if df.empty:
        return None

    df = df.copy()
    close = df['Close']
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()

    df['rsi'] = compute_rsi(close)
    compute_macd(df)
    macd_signal = detect_macd_cross(df)
    rsi_latest = df['rsi'].iloc[-1]

    msg_parts = [f"${ticker} — {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M %Z')}"]
    sent = False

    # RSI alerts
    if rsi_latest <= RSI_OVERSOLD:
        key = f"{ticker}_rsi_oversold"
        if last_alerts.get(key) != 'sent':
            msg_parts.append(f"🔔 RSI = {rsi_latest:.1f} (Oversold ≤ {RSI_OVERSOLD}) → Possible Buy")
            last_alerts[key] = 'sent'
            sent = True
    elif rsi_latest >= RSI_OVERBOUGHT:
        key = f"{ticker}_rsi_overbought"
        if last_alerts.get(key) != 'sent':
            msg_parts.append(f"⚠️ RSI = {rsi_latest:.1f} (Overbought ≥ {RSI_OVERBOUGHT}) → Possible Sell")
            last_alerts[key] = 'sent'
            sent = True
    else:
        last_alerts.pop(f"{ticker}_rsi_oversold", None)
        last_alerts.pop(f"{ticker}_rsi_overbought", None)

    # MACD alerts
    if macd_signal == 'bullish':
        key = f"{ticker}_macd_bullish"
        if last_alerts.get(key) != 'sent':
            msg_parts.append("📈 MACD crossover detected: BULLISH")
            last_alerts[key] = 'sent'
            sent = True
    elif macd_signal == 'bearish':
        key = f"{ticker}_macd_bearish"
        if last_alerts.get(key) != 'sent':
            msg_parts.append("📉 MACD crossover detected: BEARISH")
            last_alerts[key] = 'sent'
            sent = True
    else:
        last_alerts.pop(f"{ticker}_macd_bullish", None)
        last_alerts.pop(f"{ticker}_macd_bearish", None)

    if sent:
        return "\n".join(msg_parts)
    return None

def post_tweet(msg):
    """Post tweet safely with retry on rate limit."""
    try:
        client.create_tweet(text=msg)
        logger.info(f"Tweeted alert:\n{msg}")
    except tweepy.errors.TooManyRequests:
        logger.warning("Twitter rate limit reached. Sleeping for 60s...")
        time.sleep(60)
        post_tweet(msg)
    except Exception as e:
        logger.error(f"Error posting tweet: {e}")

def main_loop():
    logger.info("Starting Stock Alert Bot (Twitter)...")
    while tickers:
        try:
            for i in range(0, len(tickers), BATCH_SIZE):
                batch = tickers[i:i + BATCH_SIZE]
                logger.info(f"Processing batch: {batch}")
                df_batch = fetch_data_batch(batch)

                for ticker in batch:
                    if ticker not in df_batch:
                        continue
                    msg = analyze_ticker(ticker, df_batch[ticker])
                    if msg:
                        post_tweet(msg)
                        time.sleep(TWEET_DELAY_SECONDS)

            logger.info(f"Sleeping {CHECK_INTERVAL_SECONDS}s before next check...")
            time.sleep(CHECK_INTERVAL_SECONDS)

        except Exception as e:
            logger.exception(f"Error in main loop: {e}")
            time.sleep(CHECK_INTERVAL_SECONDS)

    logger.info("No tickers left to monitor. Exiting bot.")

if __name__ == "__main__":
    main_loop()
