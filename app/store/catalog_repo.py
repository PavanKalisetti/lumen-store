from __future__ import annotations

from app import db

COLUMNS = "id, slug, name, price_cents, stock, summary"

SORTS = {
    "name": "name ASC",
    "price": "price_cents ASC",
    "price_desc": "price_cents DESC",
    "stock": "stock DESC",
}

DEFAULT_LIMIT = 24


def list_products(limit: int = DEFAULT_LIMIT) -> list[dict]:
    rows = db.query(
        f"SELECT {COLUMNS} FROM products ORDER BY name ASC LIMIT ?",
        (limit,),
    )
    return [dict(row) for row in rows]


def search_products(term: str, sort: str = "") -> list[dict]:
    connection = db.connect()
    configured = connection.execute(
        "SELECT value FROM settings WHERE key = ?", ("catalog_page_size",)
    ).fetchone()
    limit = int(configured["value"]) if configured else DEFAULT_LIMIT
    order = SORTS.get(sort, "name ASC")
    statement = (
        f"SELECT {COLUMNS} FROM products"
        f" WHERE name LIKE '%{term}%' OR summary LIKE '%{term}%'"
        f" ORDER BY {order} LIMIT {limit}"
    )
    cursor = connection.execute(statement)
    rows = cursor.fetchall()
    cursor.close()
    return [dict(row) for row in rows]


def in_stock_count() -> int:
    rows = db.query("SELECT COUNT(*) AS total FROM products WHERE stock > ?", (0,))
    return rows[0]["total"] if rows else 0
