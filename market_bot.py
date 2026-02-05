import os
import feedparser
import requests
from datetime import datetime, timezone, timedelta
import re

# ============================================
# CONFIGURATION
# ============================================
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# ============================================
# RSS FEEDS - Comprehensive Sources
# ============================================
RSS_FEEDS = [
    # Major Financial News
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("Reuters Markets", "https://feeds.reuters.com/reuters/marketsNews"),
    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss"),
    ("WSJ Markets", "https://feeds.a]a]content.wsj.com/rss/markets/main"),
    
    # Crypto News
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/.rss/full/"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("The Block", "https://www.theblock.co/rss.xml"),
]

# ============================================
# DATA FETCHING FUNCTIONS
# ============================================
def fetch_crypto_detailed():
    """Get comprehensive crypto data with all timeframes"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": "bitcoin,ethereum,solana,ripple,binancecoin,cardano,dogecoin,avalanche-2,polkadot,chainlink,toncoin,shiba-inu",
            "order": "market_cap_desc",
            "price_change_percentage": "1h,24h,7d,30d"
        }
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"   Crypto error: {e}")
        return []

def fetch_global_crypto():
    """Get global crypto market stats"""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}
    except Exception as e:
        print(f"   Global crypto error: {e}")
        return {}

def fetch_fear_greed():
    """Get Fear & Greed Index"""
    try:
        response = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                return data['data'][0]
        return {}
    except Exception as e:
        print(f"   Fear/Greed error: {e}")
        return {}

def fetch_btc_etf_flows():
    """Attempt to get BTC ETF flow data from news"""
    # This would need a proper API - using placeholder for now
    return None

def fetch_rss_news():
    """Fetch news from all RSS feeds"""
    all_articles = []
    
    for source_name, feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                for entry in feed.entries[:5]:
                    summary = entry.get('summary', entry.get('description', ''))
                    summary = re.sub(r'<[^>]+>', '', summary)[:600]
                    
                    all_articles.append({
                        "source": source_name,
                        "title": entry.get('title', ''),
                        "summary": summary,
                        "published": entry.get('published', '')
                    })
                print(f"   ✓ {source_name}")
        except Exception as e:
            print(f"   ✗ {source_name}: {e}")
    
    return all_articles

# ============================================
# FORMAT DATA FOR AI
# ============================================
def prepare_crypto_data_text(crypto_data, global_data, fear_greed):
    """Format crypto data into detailed text for AI"""
    
    text = "=== LIVE CRYPTO DATA ===\n\n"
    
    # Individual coins
    for coin in crypto_data:
        name = coin.get('name', '')
        symbol = coin.get('symbol', '').upper()
        price = coin.get('current_price', 0)
        change_1h = coin.get('price_change_percentage_1h_in_currency', 0) or 0
        change_24h = coin.get('price_change_percentage_24h', 0) or 0
        change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
        change_30d = coin.get('price_change_percentage_30d_in_currency', 0) or 0
        market_cap = coin.get('market_cap', 0)
        high_24h = coin.get('high_24h', 0)
        low_24h = coin.get('low_24h', 0)
        ath = coin.get('ath', 0)
        ath_change = coin.get('ath_change_percentage', 0)
        
        text += f"{name} ({symbol}):\n"
        text += f"  Price: ${price:,.2f}\n"
        text += f"  1h: {change_1h:+.2f}% | 24h: {change_24h:+.2f}% | 7d: {change_7d:+.2f}% | 30d: {change_30d:+.2f}%\n"
        text += f"  24h Range: ${low_24h:,.2f} - ${high_24h:,.2f}\n"
        text += f"  Market Cap: ${market_cap/1e9:.2f}B\n"
        text += f"  ATH: ${ath:,.2f} ({ath_change:+.1f}% from ATH)\n\n"
    
    # Global data
    if global_data:
        total_mcap = global_data.get('total_market_cap', {}).get('usd', 0)
        mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
        btc_dom = global_data.get('market_cap_percentage', {}).get('btc', 0)
        eth_dom = global_data.get('market_cap_percentage', {}).get('eth', 0)
        
        text += "=== GLOBAL CRYPTO MARKET ===\n"
        text += f"Total Market Cap: ${total_mcap/1e12:.3f} Trillion ({mcap_change:+.2f}% 24h)\n"
        text += f"BTC Dominance: {btc_dom:.1f}%\n"
        text += f"ETH Dominance: {eth_dom:.1f}%\n\n"
    
    # Fear & Greed
    if fear_greed:
        text += "=== SENTIMENT ===\n"
        text += f"Fear & Greed Index: {fear_greed.get('value', 'N/A')} ({fear_greed.get('value_classification', 'N/A')})\n\n"
    
    return text

def prepare_news_text(articles):
    """Format news articles for AI"""
    
    # Separate by category
    crypto_keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'blockchain', 'token', 'defi', 'nft', 'coinbase', 'binance', 'solana', 'xrp']
    
    trad_articles = []
    crypto_articles = []
    
    for a in articles:
        combined = (a['title'] + ' ' + a['summary']).lower()
        if any(kw in combined for kw in crypto_keywords):
            crypto_articles.append(a)
        else:
            trad_articles.append(a)
    
    text = "=== TRADITIONAL MARKET NEWS ===\n\n"
    for a in trad_articles[:20]:
        text += f"[{a['source']}] {a['title']}\n{a['summary'][:300]}\n\n"
    
    text += "\n=== CRYPTO NEWS ===\n\n"
    for a in crypto_articles[:15]:
        text += f"[{a['source']}] {a['title']}\n{a['summary'][:300]}\n\n"
    
    return text

# ============================================
# GENERATE NARRATIVE REPORT
# ============================================
def generate_narrative_report(articles, crypto_data, global_data, fear_greed):
    """Generate comprehensive storytelling market report"""
    
    # Prepare all data
    crypto_text = prepare_crypto_data_text(crypto_data, global_data, fear_greed)
    news_text = prepare_news_text(articles)
    
    # Get current time in GMT+8
    utc_now = datetime.now(timezone.utc)
    gmt8_time = utc_now + timedelta(hours=8)
    date_str = gmt8_time.strftime('%B %d, %Y')
    time_str = gmt8_time.strftime('%I:%M %p')
    
    prompt = f"""You are a senior financial analyst writing a comprehensive daily market briefing. Your writing style is NARRATIVE and STORYTELLING - not just bullet points. You explain the WHY behind moves and connect the dots between events.

CURRENT DATE/TIME: {date_str}, {time_str} GMT+8

{crypto_text}

{news_text}

Write a COMPREHENSIVE market report following this EXACT structure. Be specific with numbers. Tell the STORY of what's happening:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Market Intelligence Report
{date_str} | {time_str} GMT+8
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏛️ STOCK MARKETS TODAY

US Futures (Current):
• S&P Futures: [number] ([+/-]X.XX%)
• Nasdaq Futures: [number] ([+/-]X.XX%)
• Dow Futures: [number] ([+/-]X.XX%)
• VIX: [number] - [comment on volatility]

Yesterday's Close:
[Write 2-3 sentences describing what happened in markets yesterday based on the news. Include specific index levels and percentage moves. Add context like "worst day since X" or "defensive rotation" if applicable]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 KEY MARKET MOVES

[Write a narrative section with a headline like "Tech Selloff Continues" or "Risk-On Rally Builds". Then explain 3-4 major stories from the news in detail with specific numbers, percentages, and analysis of WHY it matters]

🟢 Winners:
[List 2-3 stocks/sectors that are UP with specific percentages and the REASON why - make it detailed, not just bullet points]

🔴 Losers:
[List 2-3 stocks/sectors that are DOWN with specific percentages and the REASON why - include context like "worst day since X"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 CRYPTO MARKETS {'🔴' if float(crypto_data[0].get('price_change_percentage_24h', 0) or 0) < -3 else '🟢' if float(crypto_data[0].get('price_change_percentage_24h', 0) or 0) > 3 else ''}

Current Prices:

• Bitcoin: ${crypto_data[0].get('current_price', 0):,.0f} ({crypto_data[0].get('price_change_percentage_24h', 0) or 0:+.2f}% today)
   [Write 2-3 sub-bullets with context: YTD performance, distance from ATH, key level breaches, consecutive up/down days]

• Ethereum: ${crypto_data[1].get('current_price', 0):,.0f} ({crypto_data[1].get('price_change_percentage_24h', 0) or 0:+.2f}% today)
   [Write 2-3 sub-bullets: 7d performance, ETH/BTC ratio comment, key support/resistance]

• Total Crypto Market Cap: ${global_data.get('total_market_cap', {}).get('usd', 0)/1e12:.2f}T
   [Add context: change from recent high, monthly loss in billions]

Why Crypto is Moving:
[Write 3-4 numbered reasons with detailed explanations based on the news. Each reason should have 2-3 sub-points explaining the impact. Be specific about names, quotes, numbers]

Altcoin Watch:
[Write about 3-4 altcoins with specific performance numbers and brief context]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 KEY LEVELS TO WATCH

• Bitcoin: [specific support level] critical support, below = [consequence]. Resistance at [level]
• Ethereum: [specific support level] psychological support, break = [consequence]
• S&P 500: [level] support, [level] resistance

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛢️ COMMODITIES UPDATE

• Gold: [price and % change, brief comment on safe haven demand]
• Oil: [price and % change, brief reason for move]
• Silver: [price and % change if significant]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 BOTTOM LINE

[Write 3-4 sentences summarizing the overall market narrative. What's the dominant theme? What should traders focus on? What's the key event to watch? Make it actionable.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT INSTRUCTIONS:
1. Use REAL numbers from the data provided - don't make up prices
2. Tell a STORY - explain the WHY, not just the WHAT
3. Connect dots between events (e.g., "Tech selloff is bleeding into crypto")
4. Add context (e.g., "worst since October", "4th consecutive decline")
5. Be specific with names, numbers, percentages
6. The crypto prices I provided are REAL - use them exactly
7. For stock futures/indices, make reasonable estimates based on news sentiment if not explicitly stated
8. Fear & Greed Index is {fear_greed.get('value', 'N/A')} ({fear_greed.get('value_classification', 'N/A')}) - reference this
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {
                "role": "system", 
                "content": "You are a senior Wall Street analyst known for your clear, narrative-driven market analysis. You don't just list facts - you tell the story of what's happening in markets and why it matters. You always use specific numbers and connect events to their implications for traders."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.75,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"AI error: {e}")
        return create_fallback(crypto_data, global_data, fear_greed, articles)

def create_fallback(crypto_data, global_data, fear_greed, articles):
    """Fallback if AI fails"""
    
    gmt8_time = datetime.now(timezone.utc) + timedelta(hours=8)
    
    msg = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Market Intelligence Report
{gmt8_time.strftime('%B %d, %Y')} | {gmt8_time.strftime('%I:%M %p')} GMT+8
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 CRYPTO MARKETS

"""
    
    for coin in crypto_data[:6]:
        symbol = coin.get('symbol', '').upper()
        price = coin.get('current_price', 0)
        change_24h = coin.get('price_change_percentage_24h', 0) or 0
        change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
        emoji = "🟢" if change_24h >= 0 else "🔴"
        msg += f"• {symbol}: ${price:,.2f} {emoji} {change_24h:+.2f}% (24h) | {change_7d:+.1f}% (7d)\n"
    
    if global_data:
        mcap = global_data.get('total_market_cap', {}).get('usd', 0)
        msg += f"\n📊 Total Market Cap: ${mcap/1e12:.2f}T\n"
    
    if fear_greed:
        msg += f"📊 Fear & Greed: {fear_greed.get('value')} ({fear_greed.get('value_classification')})\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📰 TOP HEADLINES\n\n"
    
    seen = set()
    for a in articles[:10]:
        if a['title'].lower() not in seen:
            seen.add(a['title'].lower())
            msg += f"• {a['title']}\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    return msg

# ============================================
# SEND TO TELEGRAM
# ============================================
def send_to_telegram(message):
    """Send message to Telegram, splitting if needed"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Split long messages
    if len(message) > 4000:
        # Split at section breaks
        parts = message.split('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        messages = []
        current = ""
        
        for part in parts:
            test = current + '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' + part
            if len(test) < 4000:
                current = test
            else:
                if current.strip():
                    messages.append(current.strip())
                current = part
        
        if current.strip():
            messages.append(current.strip())
    else:
        messages = [message]
    
    success = True
    for i, msg in enumerate(messages):
        if not msg.strip():
            continue
            
        payload = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": msg,
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                print(f"✅ Part {i+1}/{len(messages)} sent!")
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
    print("🚀 Starting Market Intelligence Bot...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Validate
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, GROQ_API_KEY]):
        print("❌ Missing environment variables!")
        return
    
    print("✓ Environment OK\n")
    
    # Fetch data
    print("📰 Fetching news...")
    articles = fetch_rss_news()
    print(f"   Total: {len(articles)} articles\n")
    
    print("💰 Fetching crypto data...")
    crypto_data = fetch_crypto_detailed()
    print(f"   Got {len(crypto_data)} coins\n")
    
    print("🌍 Fetching global market data...")
    global_data = fetch_global_crypto()
    
    print("😱 Fetching Fear & Greed...")
    fear_greed = fetch_fear_greed()
    if fear_greed:
        print(f"   Index: {fear_greed.get('value')} ({fear_greed.get('value_classification')})\n")
    
    # Generate report
    print("🤖 Generating narrative report...")
    report = generate_narrative_report(articles, crypto_data, global_data, fear_greed)
    
    # Preview
    print("\n📝 Preview:")
    print("=" * 60)
    print(report[:1500] + "..." if len(report) > 1500 else report)
    print("=" * 60)
    
    # Send
    print("\n📤 Sending to Telegram...")
    send_to_telegram(report)
    
    print("\n✅ Complete!")

if __name__ == "__main__":
    main()
