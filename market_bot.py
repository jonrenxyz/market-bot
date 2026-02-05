import os
import feedparser
import requests
from datetime import datetime, timezone
import re
import json

# ============================================
# CONFIGURATION
# ============================================
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# ============================================
# RSS FEEDS
# ============================================
RSS_FEEDS = [
    # Traditional Markets
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("Reuters Markets", "https://feeds.reuters.com/reuters/marketsNews"),
    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss"),
    
    # Crypto News
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/.rss/full/"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("The Block", "https://www.theblock.co/rss.xml"),
]

# ============================================
# FETCH CRYPTO DATA (CoinGecko)
# ============================================
def fetch_crypto_data():
    """Get comprehensive crypto data"""
    try:
        # Main coins
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": "bitcoin,ethereum,solana,ripple,binancecoin,cardano,dogecoin,avalanche-2,polkadot,chainlink",
            "order": "market_cap_desc",
            "price_change_percentage": "1h,24h,7d,30d"
        }
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"   Crypto data error: {e}")
        return []

def fetch_global_crypto_data():
    """Get global crypto market data"""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}
    except Exception as e:
        print(f"   Global crypto error: {e}")
        return {}

def fetch_fear_greed_index():
    """Get crypto fear and greed index"""
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                return data['data'][0]
        return {}
    except Exception as e:
        print(f"   Fear/Greed error: {e}")
        return {}

# ============================================
# FETCH NEWS
# ============================================
def fetch_rss_news():
    """Fetch latest news from RSS feeds"""
    all_articles = []
    
    for source_name, feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                for entry in feed.entries[:4]:
                    summary = entry.get('summary', entry.get('description', ''))
                    summary = re.sub(r'<[^>]+>', '', summary)[:500]
                    
                    article = {
                        "source": source_name,
                        "title": entry.get('title', ''),
                        "summary": summary,
                    }
                    all_articles.append(article)
                print(f"   ✓ {source_name}")
        except Exception as e:
            print(f"   ✗ {source_name}: {e}")
    
    return all_articles

# ============================================
# FORMAT CRYPTO DATA
# ============================================
def format_crypto_section(crypto_data, global_data, fear_greed):
    """Format crypto data into readable text"""
    
    crypto_text = ""
    
    # Main prices
    for coin in crypto_data:
        symbol = coin.get('symbol', '').upper()
        price = coin.get('current_price', 0)
        change_24h = coin.get('price_change_percentage_24h', 0) or 0
        change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
        change_30d = coin.get('price_change_percentage_30d_in_currency', 0) or 0
        market_cap = coin.get('market_cap', 0)
        
        direction = "🟢" if change_24h >= 0 else "🔴"
        
        if symbol in ['BTC', 'ETH', 'SOL', 'XRP', 'BNB']:
            crypto_text += f"• {symbol}: ${price:,.2f} {direction} {change_24h:+.2f}% (24h) | {change_7d:+.1f}% (7d) | {change_30d:+.1f}% (30d)\n"
            if market_cap:
                crypto_text += f"  Market Cap: ${market_cap/1e9:.1f}B\n"
    
    # Global data
    if global_data:
        total_mcap = global_data.get('total_market_cap', {}).get('usd', 0)
        mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
        btc_dom = global_data.get('market_cap_percentage', {}).get('btc', 0)
        
        crypto_text += f"\n📊 Total Crypto Market Cap: ${total_mcap/1e12:.2f}T ({mcap_change:+.2f}% 24h)\n"
        crypto_text += f"📊 BTC Dominance: {btc_dom:.1f}%\n"
    
    # Fear & Greed
    if fear_greed:
        value = fear_greed.get('value', 'N/A')
        classification = fear_greed.get('value_classification', 'N/A')
        crypto_text += f"📊 Fear & Greed Index: {value} ({classification})\n"
    
    return crypto_text

# ============================================
# GENERATE AI SUMMARY
# ============================================
def generate_comprehensive_summary(articles, crypto_data, global_data, fear_greed):
    """Use Groq AI to generate comprehensive market summary"""
    
    # Prepare crypto data text
    crypto_info = format_crypto_section(crypto_data, global_data, fear_greed)
    
    # Separate news
    crypto_keywords = ['bitcoin', 'crypto', 'ethereum', 'btc', 'eth', 'token', 'defi', 'blockchain', 'coinbase', 'binance']
    
    trad_articles = []
    crypto_articles = []
    
    for a in articles:
        text = (a['title'] + ' ' + a['summary']).lower()
        if any(kw in text for kw in crypto_keywords):
            crypto_articles.append(a)
        else:
            trad_articles.append(a)
    
    # Build news text
    trad_news = "\n".join([f"- [{a['source']}] {a['title']}: {a['summary'][:200]}" for a in trad_articles[:15]])
    crypto_news = "\n".join([f"- [{a['source']}] {a['title']}: {a['summary'][:200]}" for a in crypto_articles[:10]])
    
    # Get time
    utc_now = datetime.now(timezone.utc)
    gmt8_hour = (utc_now.hour + 8) % 24
    time_str = f"{gmt8_hour}:00"
    date_str = datetime.now().strftime('%B %d, %Y')
    time_of_day = "Morning" if gmt8_hour < 12 else "Evening"
    
    prompt = f"""You are a senior financial analyst creating a comprehensive daily market briefing. 

CURRENT CRYPTO DATA:
{crypto_info}

TRADITIONAL MARKET NEWS:
{trad_news}

CRYPTO NEWS:
{crypto_news}

Create a DETAILED market report using this EXACT format. Be specific with numbers, percentages, and analysis:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 MARKET PULSE - {time_of_day} Edition
{date_str} | {time_str} GMT+8
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏛️ STOCK MARKETS

US Futures (Current):
• S&P 500 Futures: [estimate based on news sentiment]
• Nasdaq Futures: [estimate based on news sentiment]
• Dow Futures: [estimate based on news sentiment]

Key Market Moves:
[Analyze the news and identify 3-4 major stock stories - earnings, major moves, sector rotation]

Winners Today:
• [List 2-3 stocks that are up with reasons]

Losers Today:
• [List 2-3 stocks that are down with reasons]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 CRYPTO MARKETS

Current Prices:
{crypto_info}

Why Crypto is Moving:
[Analyze crypto news and list 3-4 key reasons for current price action]

Key Levels to Watch:
• Bitcoin: [identify support/resistance levels based on price]
• Ethereum: [identify support/resistance levels based on price]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 KEY INSIGHTS

[Write 3-4 actionable insights combining both traditional and crypto markets. What should traders watch? What's the sentiment? Any opportunities?]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ WATCH TODAY

• [List 2-3 specific events/earnings/data releases to watch]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 BOTTOM LINE

[Write a 2-3 sentence summary of overall market sentiment and what traders should focus on]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Be specific with numbers. Use actual data provided. Make it actionable for traders."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a senior financial analyst at a major investment bank. Provide detailed, data-driven market analysis. Always be specific with numbers and percentages. Your audience is active traders and investors."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=90
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"AI error: {e}")
        return create_fallback_summary(crypto_data, global_data, fear_greed, articles)

def create_fallback_summary(crypto_data, global_data, fear_greed, articles):
    """Fallback if AI fails"""
    
    utc_now = datetime.now(timezone.utc)
    gmt8_hour = (utc_now.hour + 8) % 24
    time_of_day = "Morning" if gmt8_hour < 12 else "Evening"
    date_str = datetime.now().strftime('%B %d, %Y')
    
    msg = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 MARKET PULSE - {time_of_day} Edition
{date_str} | {gmt8_hour}:00 GMT+8
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 CRYPTO PRICES

"""
    
    for coin in crypto_data[:6]:
        symbol = coin.get('symbol', '').upper()
        price = coin.get('current_price', 0)
        change_24h = coin.get('price_change_percentage_24h', 0) or 0
        direction = "🟢" if change_24h >= 0 else "🔴"
        msg += f"• {symbol}: ${price:,.2f} {direction} {change_24h:+.2f}%\n"
    
    if global_data:
        total_mcap = global_data.get('total_market_cap', {}).get('usd', 0)
        msg += f"\n📊 Total Market Cap: ${total_mcap/1e12:.2f}T\n"
    
    if fear_greed:
        msg += f"📊 Fear & Greed: {fear_greed.get('value', 'N/A')} ({fear_greed.get('value_classification', 'N/A')})\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📰 TOP HEADLINES\n\n"
    
    seen = set()
    count = 0
    for a in articles:
        if count >= 8:
            break
        if a['title'].lower() not in seen:
            seen.add(a['title'].lower())
            msg += f"• {a['title']}\n"
            count += 1
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    return msg

# ============================================
# SEND TO TELEGRAM
# ============================================
def send_to_telegram(message):
    """Send message to Telegram (split if too long)"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Telegram limit is 4096 chars - split if needed
    messages = []
    if len(message) > 4000:
        # Split at section breaks
        parts = message.split('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        current = ""
        for part in parts:
            if len(current) + len(part) + 35 < 4000:
                current += part + '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
            else:
                if current:
                    messages.append(current.strip('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━').strip())
                current = part + '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
        if current:
            messages.append(current.strip('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━').strip())
    else:
        messages = [message]
    
    success = True
    for i, msg in enumerate(messages):
        payload = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": msg,
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                print(f"✅ Message {i+1}/{len(messages)} sent!")
            else:
                print(f"❌ Error: {response.text}")
                success = False
        except Exception as e:
            print(f"❌ Error: {e}")
            success = False
    
    return success

# ============================================
# MAIN
# ============================================
def main():
    print("🚀 Starting Market Updates Bot...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Validate env vars
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, GROQ_API_KEY]):
        print("❌ Missing environment variables!")
        return
    
    print("✓ Environment variables OK")
    
    # Fetch all data
    print("\n📰 Fetching news...")
    articles = fetch_rss_news()
    print(f"   Total: {len(articles)} articles")
    
    print("\n💰 Fetching crypto data...")
    crypto_data = fetch_crypto_data()
    print(f"   Got {len(crypto_data)} coins")
    
    print("\n🌍 Fetching global crypto data...")
    global_data = fetch_global_crypto_data()
    
    print("\n😱 Fetching Fear & Greed Index...")
    fear_greed = fetch_fear_greed_index()
    if fear_greed:
        print(f"   Index: {fear_greed.get('value')} ({fear_greed.get('value_classification')})")
    
    # Generate summary
    print("\n🤖 Generating comprehensive summary...")
    summary = generate_comprehensive_summary(articles, crypto_data, global_data, fear_greed)
    
    # Preview
    print("\n📝 Preview (first 800 chars):")
    print("-" * 50)
    print(summary[:800])
    print("-" * 50)
    
    # Send
    print("\n📤 Sending to Telegram...")
    send_to_telegram(summary)
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
