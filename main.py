import os
import logging
import atexit
from datetime import datetime
from pytz import timezone
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from dotenv import load_dotenv  # Only used locally

import os

# Load .env in development (ignored in Railway)
if os.getenv("RAILWAY_ENVIRONMENT") is None:
    load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug logging
logger.info(f"Environment check:")
logger.info(f"BOT_TOKEN exists: {'BOT_TOKEN' in os.environ}")
logger.info(f"BOT_TOKEN value length: {len(os.getenv('BOT_TOKEN', ''))}")
logger.info(f"CHAT_ID exists: {'CHAT_ID' in os.environ}")
logger.info(f"CHAT_ID value: {os.getenv('CHAT_ID', 'NOT_SET')}")

# Get secrets from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN and CHAT_ID must be set as environment variables.")

bot = Bot(token=BOT_TOKEN)
chat_id = int(CHAT_ID)

# The message to send
MESSAGE = """Hello Aaron.  
שלום אהרן.  
Shalom Aaron.

Will we have a lesson on the 4th of November? 
האם נערוך שיעור ב-4 בנובמבר?  
Ha'im na'aroch shi'ur be-4 be-November?"""

MOSCOW_TZ = timezone("Europe/Moscow")

def send_telegram_message(text: str):
    try:
        bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Message sent at {datetime.now(MOSCOW_TZ)}")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

def schedule_reminders():
    scheduler = BackgroundScheduler(timezone=MOSCOW_TZ)
    
    # Schedule for Nov 1, 2, 3 at 16:00 Moscow time
    current_year = datetime.now(MOSCOW_TZ).year
    for day in [1, 2, 3]:
        run_date = MOSCOW_TZ.localize(datetime(current_year, 11, day, 16, 0, 0))
        # If the date is in the past, schedule for next year
        if run_date < datetime.now(MOSCOW_TZ):
            run_date = run_date.replace(year=current_year + 1)
        scheduler.add_job(send_telegram_message, 'date', run_date=run_date, args=[MESSAGE])
        logger.info(f"Scheduled reminder for {run_date}")
    
    scheduler.start()
    logger.info("Scheduler started.")
    
    # Ensure scheduler shuts down gracefully
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler

# Determine environment
env_name = "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"

# Send startup message
send_telegram_message(f"✅ Bot activated on {env_name}! Reminder scheduled for Nov 1–3 at 16:00 Moscow time.")

# Schedule the reminders
scheduler = schedule_reminders()

# Flask app to keep Railway happy
app = Flask(__name__)

@app.route("/")
def health_check():
    return {"status": "running", "time": datetime.now(MOSCOW_TZ).isoformat()}

# Railway will set PORT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
