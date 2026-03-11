from celery import Celery
from flask_caching import Cache
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
celery = Celery(__name__)


def init_celery(app):
    celery.conf.update(app.config["CELERY"])
    celery.conf.broker_url = app.config["CELERY"]["broker_url"]
    celery.conf.result_backend = app.config["CELERY"]["result_backend"]

    beat_entries = {}
    for name, entry in app.config["CELERY"]["beat_schedule"].items():
        schedule_cfg = entry["schedule"]
        if schedule_cfg["type"] == "crontab":
            from celery.schedules import crontab

            beat_entries[name] = {
                "task": entry["task"],
                "schedule": crontab(
                    minute=schedule_cfg.get("minute", "*"),
                    hour=schedule_cfg.get("hour", "*"),
                    day_of_month=schedule_cfg.get("day_of_month", "*"),
                ),
            }
    celery.conf.beat_schedule = beat_entries

    class FlaskTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = FlaskTask
    return celery
