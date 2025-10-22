import os
import logging
import asyncio
import atexit
from datetime import datetime
from pytz import timezone
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from dotenv import load_dotenv

# Load .env in development (ignored in Railway)
if os.getenv("RAILWAY_ENVIRONMENT") is None:
    load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug logging
logger.info(f"Environment check:")
logger.info(f"BOT_TOKEN exists: {'BOT_TOKEN' in os.environ}")
logger.info(f"BOT_TOKEN length: {len(os.getenv('BOT_TOKEN', ''))}")
logger.info(f"CHAT_ID exists: {'CHAT_ID' in os.environ}")
logger.info(f"CHAT_ID value: {os.getenv('CHAT_ID', 'NOT_SET')}")
logger.info(f"CHAT_ID_2 exists: {'CHAT_ID_2' in os.environ}")
logger.info(f"CHAT_ID_2 value: {os.getenv('CHAT_ID_2', 'NOT_SET')}")

# Get secrets from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHAT_ID_2 = os.getenv("CHAT_ID_2")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set as an environment variable.")
if not CHAT_ID:
    raise ValueError("CHAT_ID must be set as an environment variable.")
if not CHAT_ID_2:
    raise ValueError("CHAT_ID_2 must be set as an environment variable.")

bot = Bot(token=BOT_TOKEN)

# Messages
MESSAGE_1 = """Hello Aaron.  
שלום אהרן.  
Shalom Aaron.

Will we have a lesson on the 4th of November? 
האם נערוך שיעור ב-4 בנובמבר?  
Ha'im na'aroch shi'ur be-4 be-November?"""

MESSAGE_2 = "Hi guys, will we have a lesson this Wednesday, or would you prefer Wednesday the 12th? Привіт, хлопці! У нас буде урок у цю середу, чи ви хотіли б середу 12-го? - Ćao, društvo! Da li ćemo imati čas ove srede, ili biste radije u sredu 12.?"

MOSCOW_TZ = timezone("Europe/Moscow")


def send_telegram_message(chat_id: int, text: str):
    """Synchronously send a Telegram message using asyncio.run."""
    async def _send():
        try:
            await bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Message sent to {chat_id} at {datetime.now(MOSCOW_TZ)}")
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")

    asyncio.run(_send())


def schedule_reminders():
    scheduler = BackgroundScheduler(timezone=MOSCOW_TZ)
    current_year = datetime.now(MOSCOW_TZ).year

    # Parse chat IDs once
    try:
        cid1 = int(CHAT_ID)
        cid2 = int(CHAT_ID_2)
    except ValueError as e:
        logger.error(f"Invalid chat ID format: {e}")
        raise

    # Schedule for Nov 1, 2, 3 at 16:00 Moscow time
    for day in [1, 2, 3]:
        run_date = MOSCOW_TZ.localize(datetime(current_year, 11, day, 16, 0, 0))
        if run_date < datetime.now(MOSCOW_TZ):
            run_date = run_date.replace(year=current_year + 1)

        # Schedule both messages at the same time
        scheduler.add_job(send_telegram_message, 'date', run_date=run_date, args=[cid1, MESSAGE_1])
        scheduler.add_job(send_telegram_message, 'date', run_date=run_date, args=[cid2, MESSAGE_2])
        logger.info(f"Scheduled reminders for {run_date} to both chats")

    scheduler.start()
    logger.info("Scheduler started.")

    atexit.register(lambda: scheduler.shutdown())
    return scheduler


# Determine environment
env_name = "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"

# Send startup confirmation to both chats
try:
    send_telegram_message(int(CHAT_ID), f"✅ Bot activated on {env_name}! Reminder scheduled for Nov 1–3 at 16:00 Moscow time.")
    send_telegram_message(int(CHAT_ID_2), f"✅ Group reminder bot active on {env_name}! Messages scheduled for Nov 1–3 at 16:00 Moscow time.")
except Exception as e:
    logger.error(f"Failed to send startup messages: {e}")

# Schedule the reminders
scheduler = schedule_reminders()

# Flask app for Railway health check
app = Flask(__name__)

@app.route("/")
def health_check():
    return {"status": "running", "time": datetime.now(MOSCOW_TZ).isoformat()}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
