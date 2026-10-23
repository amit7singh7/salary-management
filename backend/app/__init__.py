from __future__ import annotations
import os
from flask import Flask

from . import db


def create_app(config: dict | None = None) -> Flask:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(base), "frontend"),
        static_url_path="",
    )
    app.config["DATABASE"] = os.environ.get("DATABASE", os.path.join(base, "salary.db"))
    if config:
        app.config.update(config)

    conn = db.connect(app.config["DATABASE"])
    db.init_schema(conn)
    conn.close()
    app.teardown_appcontext(db.close_db)

    from .api import bp
    app.register_blueprint(bp)

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    return app
