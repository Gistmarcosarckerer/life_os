from flask import Flask

from config import config
from backend.database import init_db, session_scope
from backend.routes.auth import auth_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.finance import finance_bp
from backend.routes.inbox import inbox_bp
from backend.routes.productivity import productivity_bp
from backend.routes.tasks import tasks_bp
from backend.routes.telegram import telegram_bp
from backend.services.background_tracker import (
    background_activity_tracker,
    should_start_background_tracker,
)
from backend.services.decision_engine import seed_default_tasks
from backend.services.finance_service import seed_financial_defaults
from backend.services.security_service import configure_security
from backend.services.telegram_bot import telegram_bot_service


def create_app():
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static",
        static_url_path="/static",
    )
    app.config["SECRET_KEY"] = config.SECRET_KEY
    configure_security(app)

    init_db()
    with session_scope() as session:
        seed_default_tasks(session)
        seed_financial_defaults(session)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(inbox_bp)
    app.register_blueprint(productivity_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(telegram_bp)

    if should_start_background_tracker():
        background_activity_tracker.start()

    telegram_bot_service.start()

    @app.route("/healthz")
    def healthz():
        return {"status": "ok", "service": "life-os"}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=False, use_reloader=False)
