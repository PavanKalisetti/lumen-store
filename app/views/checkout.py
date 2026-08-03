from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for

from app import markers
from app.store import checkout_repo
from app.views.auth import login_required

bp = Blueprint("checkout", __name__)


@bp.get("/cart")
@login_required
def cart():
    user_id = session["user_id"]
    lines = checkout_repo.cart_lines(user_id)
    return render_template(
        "checkout/cart.html",
        lines=lines,
        total_cents=sum(line["line_total_cents"] for line in lines),
    )


@bp.post("/cart/add")
@login_required
def add():
    quantity = request.form.get("quantity", type=int) or 1
    if quantity < 1:
        quantity = 1
    checkout_repo.add_to_cart(session["user_id"], request.form.get("slug", ""), quantity)
    return redirect(url_for("checkout.cart"))


@bp.get("/checkout")
@login_required
def review():
    user_id = session["user_id"]
    lines = checkout_repo.cart_lines(user_id)
    salt = checkout_repo.new_salt()
    session["checkout_salt"] = salt
    return render_template("checkout/review.html", lines=lines, salt=salt, error=None)


@bp.post("/checkout/confirm")
@login_required
def confirm():
    user_id = session["user_id"]
    total_cents = request.form.get("total_cents", type=int)
    nonce = request.form.get("nonce", "")
    salt = session.get("checkout_salt", "")
    reference = None
    if total_cents is not None:
        reference = checkout_repo.place_order(user_id, nonce, salt, total_cents)
    if reference is None:
        lines = checkout_repo.cart_lines(user_id)
        if not lines:
            return redirect(url_for("checkout.cart"))
        salt = checkout_repo.new_salt()
        session["checkout_salt"] = salt
        return render_template(
            "checkout/review.html",
            lines=lines,
            salt=salt,
            error="We could not confirm this basket. Please try again.",
        )
    session.pop("checkout_salt", None)
    return redirect(url_for("checkout.placed", reference=reference))


@bp.get("/orders/placed/<reference>")
@login_required
def placed(reference: str):
    order = checkout_repo.order_by_reference(session["user_id"], reference)
    if order is None:
        return redirect(url_for("checkout.cart"))
    lines = checkout_repo.order_lines(order["id"])
    items_total = sum(line["line_total_cents"] for line in lines)
    settlement = None
    if order["total_cents"] < items_total:
        settlement = markers.value("checkout")
    return render_template(
        "checkout/placed.html",
        order=order,
        lines=lines,
        items_total=items_total,
        settlement=settlement,
    )
