from __future__ import annotations

from flask import Flask

from app import markers
from app.config import Config


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    markers.load()

    from app import db

    db.build(app)
    app.teardown_appcontext(db.close)

    from app.views import auth, catalog, checkout, orders, products, support

    app.register_blueprint(catalog.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(products.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(support.bp)
    app.register_blueprint(checkout.bp)

    @app.context_processor
    def store_context() -> dict:
        rows = db.query("SELECT key, value FROM settings")
        return {"store": {row["key"]: row["value"] for row in rows}}

    return app
