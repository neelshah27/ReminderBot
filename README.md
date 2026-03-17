# NeurIPS Deadline Bot 🧠⏳

Daily Discord + SMS reminders counting down to **May 4, 2026**.

## What it does

- **Every morning at 9 AM ET** → posts a countdown + a rotating progress question in your Discord channel
- **Sends a short SMS** to you and your co-author at the same time
- Urgency emoji escalates as the deadline approaches (📅 → ⏳ → 🔥 → 🚨 → 💀)

## Quick commands

| Command      | What it does                        |
|-------------|-------------------------------------|
| `!countdown` | Check days remaining on demand      |
| `!nudge`     | Manually fire SMS to all numbers    |

## Setup (5 min)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and fill in your credentials
cp .env.example .env
# Edit .env with your Discord token, channel ID, and Twilio creds

# 3. Run
python bot.py
```

### Getting your Discord Channel ID

Right-click the channel in Discord → **Copy Channel ID**
(enable Developer Mode in Settings → Advanced if you don't see it)

### Twilio free tier

Twilio's free trial gives you ~$15 of credit — enough for months of daily texts. You just need to verify the recipient numbers first on the free tier.

## Keep it running

For always-on hosting, run it on any cheap VPS, a Raspberry Pi, or use a free tier on Railway / Render / Fly.io:

```bash
# Simple background run
nohup python bot.py &

# Or with systemd, pm2, screen, tmux, etc.
```
