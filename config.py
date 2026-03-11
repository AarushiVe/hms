import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = "sqlite:///hms.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300

    TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "12"))
    REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", "8"))

    CELERY = {
        "broker_url": REDIS_URL,
        "result_backend": REDIS_URL,
        "task_ignore_result": False,
        "timezone": os.getenv("TZ", "Asia/Kolkata"),
        "beat_schedule": {
            "daily-reminders": {
                "task": "app.tasks.send_daily_reminders",
                "schedule": {
                    "type": "crontab",
                    "minute": 0,
                    "hour": REMINDER_HOUR,
                },
            },
            "monthly-doctor-report": {
                "task": "app.tasks.send_monthly_doctor_reports",
                "schedule": {
                    "type": "crontab",
                    "minute": 0,
                    "hour": 7,
                    "day_of_month": 1,
                },
            },
        },
    }

    MAIL_WEBHOOK_URL = os.getenv("MAIL_WEBHOOK_URL", "")
    GOOGLE_CHAT_WEBHOOK_URL = os.getenv("GOOGLE_CHAT_WEBHOOK_URL", "")


class DevConfig(Config):
    DEBUG = True
