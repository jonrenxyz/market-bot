# 📊 Daily Market Updates Telegram Bot

Automated daily market briefing sent to your Telegram channel at 9:00 AM GMT+8.

## Features
- 📈 Traditional market news (stocks, indices)
- 💰 Crypto news (Bitcoin, Ethereum, DeFi)
- 🤖 AI-powered summaries with actionable insights
- ⏰ Automatic daily delivery at 9 AM GMT+8
- 💸 100% FREE hosting on GitHub Actions

---

## Quick Setup (15 minutes)

### Step 1: Get Your API Keys

| Service | How to Get | Cost |
|---------|------------|------|
| **Telegram Bot** | Message [@BotFather](https://t.me/BotFather) → `/newbot` | Free |
| **Groq AI** | [console.groq.com](https://console.groq.com) → API Keys | Free |
| **NewsData** (optional) | [newsdata.io](https://newsdata.io) → Get API Key | Free (200/day) |

### Step 2: Create Telegram Channel
1. Open Telegram → Create a new channel
2. Add your bot as **Administrator** (must have "Post Messages" permission)
3. Note your channel ID:
   - Public channel: `@yourchannelusername`
   - Private channel: Add `@userinfobot` to get the ID (starts with `-100...`)

### Step 3: Add Secrets to GitHub

Go to your repository: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets (copy-paste exactly):

| Secret Name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHANNEL_ID` | `@yourchannel` or `-100xxxxxxxxx` |
| `GROQ_API_KEY` | Your Groq API key |
| `NEWSDATA_API_KEY` | (Optional) Your NewsData.io key |

### Step 4: Test It!
1. Go to **Actions** tab in your repo
2. Click **Daily Market Updates** on the left
3. Click **Run workflow** → **Run workflow**
4. Wait 1-2 minutes
5. Check your Telegram channel! 🎉

---

## File Structure
```
market-updates-bot/
├── market_bot.py              # Main bot script
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── .github/
    └── workflows/
        └── daily-update.yml   # GitHub Actions scheduler
```

---

## Customization

### Change Schedule Time
Edit `.github/workflows/daily-update.yml`:
```yaml
schedule:
  - cron: '0 1 * * *'  # Currently 9 AM GMT+8 (1 AM UTC)
```

Common times (GMT+8):
- 8 AM: `0 0 * * *`
- 9 AM: `0 1 * * *` (default)
- 10 AM: `0 2 * * *`

---

## Troubleshooting

**Bot not posting?**
1. Check **Actions** tab for error logs
2. Make sure bot is **Admin** in channel
3. Verify all 3 required secrets are set

**"Forbidden" error?**
- Bot needs admin rights in the channel

**No news found?**
- Add `NEWSDATA_API_KEY` for better results

---

## Support
Built for daily market intelligence. Questions? Check the Actions logs for detailed errors.

