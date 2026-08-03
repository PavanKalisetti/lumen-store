from __future__ import annotations

import sqlite3

from flask import Blueprint, jsonify, render_template, request

from app.store import catalog_repo

bp = Blueprint("catalog", __name__)


@bp.get("/")
def index():
    term = request.args.get("q", "").strip()
    sort = request.args.get("sort", "")
    if term:
        products = catalog_repo.search_products(term, sort)
    else:
        products = catalog_repo.list_products()
    return render_template(
        "catalog/index.html",
        products=products,
        term=term,
        sort=sort,
        available=catalog_repo.in_stock_count(),
    )


@bp.get("/api/catalog")
def api_catalog():
    term = request.args.get("q", "").strip()
    sort = request.args.get("sort", "")
    try:
        products = catalog_repo.search_products(term, sort)
    except sqlite3.Error as exc:
        return jsonify({"q": term, "sort": sort, "error": str(exc)}), 400
    return jsonify(products)
