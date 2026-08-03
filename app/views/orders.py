from __future__ import annotations

from flask import Blueprint, abort, render_template, session

from app import markers
from app.store import orders_repo
from app.views.auth import require_login

bp = Blueprint("orders", __name__)


@bp.route("/orders")
def index():
    guard = require_login()
    if guard is not None:
        return guard
    orders = orders_repo.list_for_user(session["user_id"])
    return render_template("orders/index.html", orders=orders)


@bp.route("/orders/<reference>/receipt")
def receipt(reference: str):
    guard = require_login()
    if guard is not None:
        return guard
    record = orders_repo.find_by_reference(reference)
    if record is None:
        abort(404)
    return render_template(
        "orders/receipt.html",
        order=record["order"],
        items=record["items"],
        fulfilment_reference=markers.value("receipt"),
    )
