import os
import feedparser
import requests
from datetime import datetime, timezone
import re

# ============================================
# CONFIGURATION
# ============================================
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Multiple RSS feeds for redundancy
RSS_FEEDS = [
    # Traditional Markets
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("Reuters Markets", "https://feeds.reuters.com/reuters/marketsNews"),
    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("CNBC Top News", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    
    # Crypto News
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/.rss/full/"),
    ("Decrypt", "https://decrypt.co/feed"),
]

# Crypto prices API
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple&vs_currencies=usd&include_24hr_change=true"

# ============================================
# FETCH NEWS FROM RSS FEEDS
# ============================================
def fetch_rss_news():
    """Fetch latest news from multiple RSS feeds"""
    all_articles = []
    successful_feeds = 0
    
    for source_name, feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                successful_feeds += 1
                for entry in feed.entries[:3]:
                    summary = entry.get('summary', entry.get('description', ''))
                    summary = re.sub(r'<[^>]+>', '', summary)
                    summary = summary[:400] if summary else ''
                    
                    article = {
                        "source": source_name,
                        "title": entry.get('title', 'No title'),
                        "summary": summary,
                        "link": entry.get('link', ''),
                    }
                    all_articles.append(article)
                print(f"   ✓ {source_name}: {len(feed.entries)} articles")
        except Exception as e:
            print(f"   ✗ {source_name}: {e}")
    
    print(f"   Successfully fetched from {successful_feeds}/{len(RSS_FEEDS)} feeds")
    return all_articles

# ============================================
# FETCH CRYPTO PRICES
# ============================================
def fetch_crypto_prices():
    """Get current crypto prices from CoinGecko"""
    try:
        response = requests.get(COINGECKO_API, timeout=10)
        if response.status_code == 200:
            data = response.json()
            prices = []
            coin_symbols = {
                'bitcoin': 'BTC',
                'ethereum': 'ETH', 
                'solana': 'SOL',
                'ripple': 'XRP'
            }
            for coin, info in data.items():
                price = info.get('usd', 0)
                change = info.get('usd_24h_change', 0)
                symbol = coin_symbols.get(coin, coin.upper()[:3])
                direction = "🟢" if change >= 0 else "🔴"
                prices.append(f"{symbol}: ${price:,.2f} {direction} {change:+.1f}%")
            return prices
        return []
    except Exception as e:
        print(f"   Crypto prices error: {e}")
        return []

# ============================================
# SUMMARIZE WITH GROQ AI
# ============================================
def summarize_with_ai(articles, crypto_prices):
    """Use Groq AI to create intelligent market summary"""
    
    # Separate traditional and crypto news
    crypto_keywords = ['coin', 'crypto', 'bitcoin', 'decrypt', 'block', 'defi', 'token', 'eth']
    trad_news = [a for a in articles if not any(kw in a['source'].lower() for kw in crypto_keywords)]
    crypto_news = [a for a in articles if a not in trad_news]
    
    # Build news text
    news_text = "\n=== TRADITIONAL MARKETS ===\n"
    for i, article in enumerate(trad_news[:8], 1):
        news_text += f"{i}. [{article['source']}] {article['title']}\n"
        if article['summary']:
            news_text += f"   {article['summary'][:200]}\n"
    
    news_text += "\n=== CRYPTO NEWS ===\n"
    for i, article in enumerate(crypto_news[:8], 1):
        news_text += f"{i}. [{article['source']}] {article['title']}\n"
        if article['summary']:
            news_text += f"   {article['summary'][:200]}\n"
    
    crypto_price_text = "\n".join(crypto_prices) if crypto_prices else "Prices unavailable"
    
    # Get time of day for GMT+8
    utc_now = datetime.now(timezone.utc)
    gmt8_hour = (utc_now.hour + 8) % 24
    time_of_day = "Morning" if gmt8_hour < 12 else "Evening"
    
    prompt = f"""You are a professional financial analyst creating a daily market briefing.

CURRENT CRYPTO PRICES:
{crypto_price_text}

TODAY'S NEWS:
{news_text}

Create a market update with this EXACT format:

📊 DAILY MARKET PULSE
{time_of_day} Edition • {datetime.now().strftime('%A, %B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━

🏛️ TRADITIONAL MARKETS
• [Write 2-3 bullet points about major stock/economic moves]

💰 CRYPTO & WEB3
• [Write 2-3 bullet points about crypto news]
• Include BTC, ETH prices with 24h changes

📈 KEY INSIGHTS
• [Write 2-3 actionable insights for traders]

⚠️ WATCH TODAY
• [1-2 things to monitor]

━━━━━━━━━━━━━━━━━━━━

Keep it professional and concise. Be specific with numbers."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a professional financial market analyst."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"AI summarization error: {e}")
        return create_fallback_summary(articles, crypto_prices)

def create_fallback_summary(articles, crypto_prices):
    """Fallback if AI fails"""
    utc_now = datetime.now(timezone.utc)
    gmt8_hour = (utc_now.hour + 8) % 24
    time_of_day = "Morning" if gmt8_hour < 12 else "Evening"
    today = datetime.now().strftime('%A, %B %d, %Y')
    
    message = f"""📊 DAILY MARKET PULSE
{time_of_day} Edition • {today}

━━━━━━━━━━━━━━━━━━━━

"""
    
    if crypto_prices:
        message += "💰 CRYPTO PRICES\n"
        for price in crypto_prices:
            message += f"• {price}\n"
        message += "\n"
    
    message += "📰 TOP HEADLINES\n\n"
    
    seen_titles = set()
    count = 0
    for article in articles:
        if count >= 10:
            break
        title_lower = article['title'].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            message += f"• [{article['source']}] {article['title']}\n\n"
            count += 1
    
    message += "━━━━━━━━━━━━━━━━━━━━"
    
    return message

# ============================================
# SEND TO TELEGRAM
# ============================================
def send_to_telegram(message):
    """Send message to Telegram channel"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    if len(message) > 4000:
        message = message[:4000] + "\n\n... [truncated]"
    
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            print("✅ Message sent successfully to Telegram!")
            return True
        else:
            print(f"❌ Telegram error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

# ============================================
# MAIN EXECUTION
# ============================================
def main():
    print("🚀 Starting Market Updates Bot...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Validate environment variables
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHANNEL_ID:
        missing.append("TELEGRAM_CHANNEL_ID")
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return
    
    print("✓ All environment variables present")
    
    # Fetch news
    print("\n📰 Fetching news from RSS feeds...")
    articles = fetch_rss_news()
    print(f"   Total articles: {len(articles)}")
    
    # Fetch crypto prices
    print("\n💰 Fetching crypto prices...")
    crypto_prices = fetch_crypto_prices()
    if crypto_prices:
        print(f"   {', '.join(crypto_prices)}")
    
    if not articles and not crypto_prices:
        print("❌ No data found!")
        return
    
    # Generate AI summary
    print("\n🤖 Generating AI summary...")
    summary = summarize_with_ai(articles, crypto_prices)
    
    # Preview
    print("\n📝 Preview:")
    print("-" * 40)
    print(summary[:500] + "..." if len(summary) > 500 else summary)
    print("-" * 40)
    
    # Send to Telegram
    print("\n📤 Sending to Telegram...")
    send_to_telegram(summary)

if __name__ == "__main__":
    main()
