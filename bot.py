import time
import logging
from datetime import datetime, timezone
import yfinance as yf
import pandas as pd
import tweepy
from indicators import compute_rsi, compute_macd, detect_macd_cross
import config as cfg

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Twitter v2 Client
client = tweepy.Client(
    bearer_token=cfg.TWITTER_BEARER_TOKEN,
    consumer_key=cfg.TWITTER_API_KEY,
    consumer_secret=cfg.TWITTER_API_SECRET,
    access_token=cfg.TWITTER_ACCESS_TOKEN,
    access_token_secret=cfg.TWITTER_ACCESS_TOKEN_SECRET
)

last_alerts = {}
tickers = cfg.TICKERS.copy()

def fetch_data_batch(tickers_batch):
    """Fetch data for multiple tickers, remove delisted ones."""
    df_all = {}
    removed = []
    for ticker in tickers_batch:
        try:
            df = yf.download(
                tickers=ticker,
                period=cfg.YFINANCE_PERIOD,
                interval=cfg.YFINANCE_INTERVAL,
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
    if rsi_latest <= cfg.RSI_OVERSOLD:
        key = f"{ticker}_rsi_oversold"
        if last_alerts.get(key) != 'sent':
            msg_parts.append(f"🔔 RSI = {rsi_latest:.1f} (Oversold ≤ {cfg.RSI_OVERSOLD}) → Possible Buy")
            last_alerts[key] = 'sent'
            sent = True
    elif rsi_latest >= cfg.RSI_OVERBOUGHT:
        key = f"{ticker}_rsi_overbought"
        if last_alerts.get(key) != 'sent':
            msg_parts.append(f"⚠️ RSI = {rsi_latest:.1f} (Overbought ≥ {cfg.RSI_OVERBOUGHT}) → Possible Sell")
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
    batch_size = cfg.BATCH_SIZE

    while tickers:
        try:
            for i in range(0, len(tickers), batch_size):
                batch = tickers[i:i + batch_size]
                logger.info(f"Processing batch: {batch}")
                df_batch = fetch_data_batch(batch)

                for ticker in batch:
                    if ticker not in df_batch:
                        continue
                    msg = analyze_ticker(ticker, df_batch[ticker])
                    if msg:
                        post_tweet(msg)
                        time.sleep(getattr(cfg, "TWEET_DELAY_SECONDS", 5))  # configurable delay

            logger.info(f"Sleeping {cfg.CHECK_INTERVAL_SECONDS}s before next check...")
            time.sleep(cfg.CHECK_INTERVAL_SECONDS)

        except Exception as e:
            logger.exception(f"Error in main loop: {e}")
            time.sleep(cfg.CHECK_INTERVAL_SECONDS)

    logger.info("No tickers left to monitor. Exiting bot.")

if __name__ == "__main__":
    main_loop()
