# src/scheduler_app.py
import time
import logging
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from src.crew_lite import run_movie_review_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def job():
    logger.info("Starting scheduled movie review job...")
    run_movie_review_pipeline()
    logger.info("Job finished.")

def main():
    ist = ZoneInfo("Asia/Kolkata")
    scheduler = BackgroundScheduler(timezone=ist)
    # Saturday at 10:00 IST
    # scheduler.add_job(
    #     job,
    #     "cron",
    #     day_of_week="sat",
    #     hour=10,
    #     minute=0,
    #     id="weekly_movie_review",
    #     timezone=ist,
    # )
    # For testing: every minute
    scheduler.add_job(
        job,
        "interval",
        minutes=1,
        id="test_movie_review",
        timezone=ist,
    )
    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped.")

if __name__ == "__main__":
    main()
