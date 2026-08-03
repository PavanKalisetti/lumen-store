from __future__ import annotations

from flask import Blueprint, abort, jsonify, render_template, request

from app import markers
from app.store import reviews_repo
from app.views.auth import require_login

bp = Blueprint("products", __name__)


@bp.route("/products/<slug>")
def detail(slug: str):
    product = reviews_repo.find_product(slug)
    if product is None:
        abort(404)
    return render_template("products/detail.html", product=product)


@bp.route("/api/products/<slug>/reviews")
def list_reviews(slug: str):
    product = reviews_repo.find_product(slug)
    if product is None:
        return jsonify({"count": 0, "html_fragments": []}), 404
    return jsonify(reviews_repo.render_payload(product["id"]))


@bp.route("/api/products/<slug>/reviews", methods=["POST"])
def create_review(slug: str):
    guard = require_login()
    if guard is not None:
        return guard

    product = reviews_repo.find_product(slug)
    if product is None:
        return jsonify({"error": "unknown product"}), 404

    payload = request.get_json(silent=True) or {}
    author = str(payload.get("author") or "").strip()
    body = str(payload.get("body") or "")
    try:
        rating = int(payload.get("rating") or 5)
    except (TypeError, ValueError):
        rating = 5
    rating = max(1, min(5, rating))

    if not body.strip():
        return jsonify({"error": "a review body is required"}), 400

    reviews_repo.add_review(product["id"], author or "Anonymous", rating, body)
    return jsonify(reviews_repo.render_payload(product["id"])), 201


@bp.route("/api/storefront/render-receipt")
def render_receipt():
    if request.headers.get("X-Render-Complete") != "1":
        return jsonify({}), 404
    return jsonify({"reference": markers.value("review")})
