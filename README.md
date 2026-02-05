# Market Bot

Real-time market intelligence via Telegram powered by Claude Sonnet 4.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your keys:
```
TELEGRAM_BOT_TOKEN=your_token
ANTHROPIC_API_KEY=your_key
```

3. Run:
```bash
python bot.py
```

## Commands

- `/market` - Stock market summary
- `/crypto` - Full market + detailed crypto analysis
- `/quick` - Fast snapshot

## Features

✅ Real-time Yahoo Finance data
✅ Detailed crypto analysis with Fear & Greed Index
✅ Earnings highlights with specific guidance
✅ Support/resistance levels
✅ Expert predictions
✅ Clean markdown formatting
