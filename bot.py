"""
NeurIPS Deadline Countdown Bot
──────────────────────────────
Daily Discord reminder + SMS nudge for you and your co-author.

Setup:
  1. Create a Discord bot at https://discord.com/developers/applications
  2. Enable MESSAGE CONTENT intent under Bot settings
  3. Create a free Twilio account at https://www.twilio.com
  4. Fill in .env with your credentials
  5. pip install discord.py python-dotenv twilio
  6. python bot.py
"""

import os
import random
import asyncio
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from twilio.rest import Client as TwilioClient

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")          # your Twilio number
PHONE_NUMBERS = os.getenv("PHONE_NUMBERS", "").split(",")  # comma-separated

DEADLINE = datetime(2026, 5, 4, tzinfo=ZoneInfo("America/Toronto"))
TIMEZONE = ZoneInfo("America/Toronto")
REMINDER_HOUR = 9   # 9 AM ET
REMINDER_MINUTE = 0

# ── Progress prompts (rotated daily so it stays fresh) ────────────────────────
PROGRESS_QUESTIONS = [
    "What's the ONE thing you're finishing today?",
    "Any blockers? Drop them here so we can unblock each other.",
    "Rate your progress this week: 🔴 behind | 🟡 okay | 🟢 on track",
    "Which section of the paper needs the most work right now?",
    "Did you hit yesterday's goal? Be honest 👀",
    "What experiment are you running today?",
    "Anything you need a second pair of eyes on?",
    "Quick check — is your Related Work section up to date?",
    "Have you committed / pushed your latest code today?",
    "If the deadline were TOMORROW, what would you panic-write first?",
    "What's one thing you're stuck on that talking through might help?",
    "Drop a screenshot of your latest figure / result 📊",
    "Are your baselines finalized or still in flux?",
    "Writing or experiments today? Declare it now 🫡",
    "What's the riskiest part of your submission right now?",
]

# ── Emoji vibes based on urgency ──────────────────────────────────────────────
def get_vibe(days_left: int) -> str:
    if days_left > 30:
        return "📅"
    elif days_left > 14:
        return "⏳"
    elif days_left > 7:
        return "🔥"
    elif days_left > 3:
        return "🚨"
    elif days_left > 0:
        return "💀"
    else:
        return "🎉"


def days_until_deadline() -> int:
    now = datetime.now(TIMEZONE)
    return (DEADLINE - now).days


def build_message() -> str:
    days = days_until_deadline()
    vibe = get_vibe(days)
    question = random.choice(PROGRESS_QUESTIONS)

    if days > 0:
        header = f"{vibe}  **{days} day{'s' if days != 1 else ''} until NeurIPS deadline**  {vibe}"
    elif days == 0:
        header = f"💀  **TODAY IS DEADLINE DAY**  💀"
    else:
        header = f"🎉  **Deadline has passed — hope you submitted!**  🎉"

    return (
        f"────────────────────────────\n"
        f"☀️  **Good morning, researchers!**\n\n"
        f"{header}\n"
        f"📆  Deadline: **May 4, 2026**\n\n"
        f"💬  *{question}*\n"
        f"────────────────────────────"
    )


def build_sms() -> str:
    days = days_until_deadline()
    if days > 0:
        return f"NeurIPS countdown: {days} day(s) left until May 4! Get after it today."
    elif days == 0:
        return "NeurIPS deadline is TODAY. Submit that paper! 🚀"
    else:
        return "NeurIPS deadline has passed. Hope it went well!"


# ── Twilio SMS helper ─────────────────────────────────────────────────────────
def send_sms(body: str):
    if not all([TWILIO_SID, TWILIO_AUTH, TWILIO_FROM]):
        print("[SMS] Twilio not configured — skipping SMS.")
        return

    client = TwilioClient(TWILIO_SID, TWILIO_AUTH)
    for number in PHONE_NUMBERS:
        number = number.strip()
        if not number:
            continue
        try:
            client.messages.create(body=body, from_=TWILIO_FROM, to=number)
            print(f"[SMS] Sent to {number}")
        except Exception as e:
            print(f"[SMS] Failed for {number}: {e}")


# ── Bot setup ─────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@tasks.loop(hours=24)
async def daily_reminder():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"[ERROR] Channel {CHANNEL_ID} not found.")
        return

    # Discord message
    await channel.send(build_message())

    # SMS
    send_sms(build_sms())
    print(f"[OK] Daily reminder sent — {days_until_deadline()} days left.")


@daily_reminder.before_loop
async def wait_until_morning():
    """Sleep until the next REMINDER_HOUR so the loop fires at the right time."""
    await bot.wait_until_ready()
    now = datetime.now(TIMEZONE)
    target = now.replace(hour=REMINDER_HOUR, minute=REMINDER_MINUTE, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    wait_seconds = (target - now).total_seconds()
    print(f"[INIT] Waiting {wait_seconds:.0f}s until {target.strftime('%I:%M %p %Z')}...")
    await asyncio.sleep(wait_seconds)


# ── Manual commands ───────────────────────────────────────────────────────────
@bot.command(name="countdown")
async def countdown(ctx):
    """Check the countdown on demand."""
    await ctx.send(build_message())


@bot.command(name="nudge")
async def nudge(ctx):
    """Manually fire an SMS nudge to everyone."""
    send_sms(build_sms())
    await ctx.send("📲  SMS nudge sent to all numbers!")


@bot.event
async def on_ready():
    print(f"[READY] Logged in as {bot.user}  |  {days_until_deadline()} days to NeurIPS")
    daily_reminder.start()


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("❌  Set DISCORD_TOKEN in your .env file.")
    bot.run(DISCORD_TOKEN)
