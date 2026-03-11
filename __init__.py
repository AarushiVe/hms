from flask import Flask, render_template

from .config import DevConfig
from .extensions import cache, db, init_celery, migrate
from .models import seed_admin_and_departments


def create_app(config_class=DevConfig):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    init_celery(app)

    from .api import api_bp

    app.register_blueprint(api_bp)

    @app.route("/")
    @app.route("/login")
    @app.route("/register")
    @app.route("/dashboard")
    def index():
        return render_template("index.html")

    with app.app_context():
        db.create_all()
        seed_admin_and_departments()

        from . import tasks 

    return app
