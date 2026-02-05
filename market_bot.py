# bot.py
import os
import anthropic
import telebot
from datetime import datetime
from config import MARKET_SYSTEM_PROMPT, MAX_MESSAGE_LENGTH

# Initialize
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def call_claude_with_search(user_prompt, system_prompt):
    """Call Claude with web search capability"""
    
    try:
        # Initial request with web_search tool
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_prompt
            }],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }]
        )
        
        # Extract text from response
        text_content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                text_content += block.text
        
        return text_content
        
    except Exception as e:
        return f"❌ Error calling Claude API: {str(e)}"

def split_message(text, max_length=MAX_MESSAGE_LENGTH):
    """Split long messages by sections for Telegram"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    
    # Split by main headers first (##)
    sections = text.split('\n## ')
    current_chunk = ""
    
    for i, section in enumerate(sections):
        # Add back the ## prefix (except for first section)
        if i > 0:
            section = '## ' + section
        
        # If adding this section exceeds limit, save current chunk
        if len(current_chunk) + len(section) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = section
        else:
            current_chunk += "\n\n" + section if current_chunk else section
    
    # Add remaining content
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def send_long_message(chat_id, text):
    """Send message, splitting if necessary"""
    chunks = split_message(text)
    
    for i, chunk in enumerate(chunks):
        try:
            bot.send_message(
                chat_id, 
                chunk, 
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        except Exception as e:
            # If markdown fails, try without formatting
            try:
                bot.send_message(chat_id, chunk)
            except:
                bot.send_message(chat_id, f"❌ Error sending message part {i+1}: {str(e)}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
📊 **Market Bot - Real-Time Market Intelligence**

**Commands:**
- `/market` - Latest stock market summary
- `/crypto` - Full market + crypto analysis  
- `/quick` - Quick market snapshot

**What you get:**
✅ Real-time prices & moves
✅ Earnings highlights
✅ Sector rotation analysis
✅ Crypto deep-dive (with /crypto)
✅ Expert predictions
✅ Key levels to watch

**Example:** 
`/crypto` → Get the full market breakdown including detailed crypto analysis

Powered by Claude Sonnet 4 with real-time web search 🚀
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['market'])
def market_summary(message):
    chat_id = message.chat.id
    
    # Send working message
    status_msg = bot.send_message(chat_id, "📊 Fetching latest market data from Yahoo Finance...")
    
    try:
        # Create prompt
        now = datetime.now()
        prompt = f"""Read all the latest news today on Yahoo Finance and summarize key market moves.

Current time: {now.strftime('%B %d, %Y at %I:%M %p GMT+8')}

Provide a comprehensive market summary covering:
- Major indices (futures if pre-market, closing if after hours)
- Key sector moves and rotation themes  
- Individual stock highlights (winners/losers with specific reasons)
- Earnings reports and guidance changes
- Commodities (gold, oil)
- Bottom line: what matters most today

Use the exact formatting style specified in your instructions."""

        # Call Claude
        response = call_claude_with_search(prompt, MARKET_SYSTEM_PROMPT)
        
        # Delete status message
        bot.delete_message(chat_id, status_msg.message_id)
        
        # Send response
        send_long_message(chat_id, response)
        
    except Exception as e:
        bot.edit_message_text(
            f"❌ Error: {str(e)}", 
            chat_id, 
            status_msg.message_id
        )

@bot.message_handler(commands=['crypto'])
def crypto_summary(message):
    chat_id = message.chat.id
    
    # Send working message
    status_msg = bot.send_message(
        chat_id, 
        "📊 Fetching latest market & crypto data... This takes 30-60 seconds."
    )
    
    try:
        # Create detailed prompt
        now = datetime.now()
        prompt = f"""Read all the latest news today on Yahoo Finance and summarize key market moves AND provide detailed crypto analysis.

Current time: {now.strftime('%B %d, %Y at %I:%M %p GMT+8')}

Provide a comprehensive summary covering:

**STOCKS:**
- Major indices (futures if pre-market, closing if after hours)
- Key sector moves and rotation themes
- Individual stock highlights (winners/losers with WHY)
- Earnings reports and specific guidance numbers

**CRYPTO (DETAILED):**
- Current Bitcoin price with % changes (today, YTD, from high)
- Current Ethereum price with % changes
- Total crypto market cap and change
- Top 3-5 altcoin movers with % changes
- Specific reasons WHY crypto is moving (numbered list with details)
- Sentiment indicators (Fear & Greed Index with number)
- Support/resistance levels for BTC and ETH
- Expert forecasts if available
- Liquidation data if relevant
- Key catalysts or news

**COMMODITIES:**
- Gold, silver, oil prices

**BOTTOM LINE:**
One sentence on what matters most

Use the exact formatting style specified in your instructions with proper sections and markdown."""

        # Call Claude
        response = call_claude_with_search(prompt, MARKET_SYSTEM_PROMPT)
        
        # Delete status message
        bot.delete_message(chat_id, status_msg.message_id)
        
        # Send response
        send_long_message(chat_id, response)
        
    except Exception as e:
        bot.edit_message_text(
            f"❌ Error: {str(e)}", 
            chat_id, 
            status_msg.message_id
        )

@bot.message_handler(commands=['quick'])
def quick_summary(message):
    chat_id = message.chat.id
    
    status_msg = bot.send_message(chat_id, "⚡ Quick market snapshot...")
    
    try:
        prompt = """Give me a 200-word snapshot of markets right now:
- S&P, Nasdaq, Dow (with %)
- Top 3 movers
- What's driving moves today
- One-line bottom line

Be direct and punchy."""

        response = call_claude_with_search(prompt, MARKET_SYSTEM_PROMPT)
        
        bot.delete_message(chat_id, status_msg.message_id)
        bot.send_message(chat_id, response, parse_mode='Markdown')
        
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", chat_id, status_msg.message_id)

# Error handler
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(
        message, 
        "Use /market for stocks, /crypto for full analysis, or /help for commands."
    )

if __name__ == '__main__':
    print("🤖 Market Bot is running...")
    bot.infinity_polling()
