from __future__ import annotations

import random
import secrets
import string
from datetime import date

from app import db

STEP_LABELS = ("Cart", "Review", "Confirmation")


def derive_nonce(salt: str, total_cents: int) -> str:
    digits = str(total_cents)
    merged = []
    for index in range(max(len(salt), len(digits))):
        if index < len(salt):
            merged.append(salt[index])
        if index < len(digits):
            merged.append(digits[index])
    return "".join(f"{ord(char):02x}" for char in merged)


def new_salt() -> str:
    return secrets.token_hex(4)


def add_to_cart(user_id: int, slug: str, quantity: int) -> bool:
    connection = db.connect()
    product = connection.execute(
        "SELECT id, price_cents FROM products WHERE slug = ?", (slug,)
    ).fetchone()
    if product is None:
        return False
    existing = connection.execute(
        "SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
        (user_id, product["id"]),
    ).fetchone()
    if existing is None:
        connection.execute(
            "INSERT INTO cart_items (user_id, product_id, quantity, unit_price_cents)"
            " VALUES (?, ?, ?, ?)",
            (user_id, product["id"], quantity, product["price_cents"]),
        )
    else:
        connection.execute(
            "UPDATE cart_items SET quantity = ?, unit_price_cents = ? WHERE id = ?",
            (existing["quantity"] + quantity, product["price_cents"], existing["id"]),
        )
    connection.commit()
    return True


def cart_lines(user_id: int) -> list[dict]:
    rows = db.query(
        "SELECT p.slug AS slug, p.name AS name, c.quantity AS quantity,"
        " c.unit_price_cents AS unit_price_cents"
        " FROM cart_items c JOIN products p ON p.id = c.product_id"
        " WHERE c.user_id = ? ORDER BY c.id",
        (user_id,),
    )
    return [
        {
            "slug": row["slug"],
            "name": row["name"],
            "quantity": row["quantity"],
            "unit_price_cents": row["unit_price_cents"],
            "line_total_cents": row["quantity"] * row["unit_price_cents"],
        }
        for row in rows
    ]


def cart_total(user_id: int) -> int:
    return sum(line["line_total_cents"] for line in cart_lines(user_id))


def _reference() -> str:
    digits = "".join(random.choice(string.digits) for _ in range(4))
    letters = "".join(random.choice(string.ascii_uppercase) for _ in range(2))
    return f"LM-{digits}-{letters}"


def place_order(user_id: int, nonce: str, salt: str, total_cents: int) -> str | None:
    if not salt or derive_nonce(salt, total_cents) != nonce:
        return None

    connection = db.connect()
    lines = connection.execute(
        "SELECT p.name AS name, c.quantity AS quantity, c.unit_price_cents AS unit_price_cents"
        " FROM cart_items c JOIN products p ON p.id = c.product_id"
        " WHERE c.user_id = ? ORDER BY c.id",
        (user_id,),
    ).fetchall()
    if not lines:
        return None

    shopper = connection.execute(
        "SELECT display_name FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    reference = _reference()
    cursor = connection.execute(
        "INSERT INTO orders (user_id, reference, total_cents, status, ship_name,"
        " ship_address, placed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            reference,
            total_cents,
            "placed",
            shopper["display_name"] if shopper else "",
            "",
            date.today().isoformat(),
        ),
    )
    order_id = cursor.lastrowid
    for line in lines:
        connection.execute(
            "INSERT INTO order_items (order_id, name, quantity, unit_price_cents)"
            " VALUES (?, ?, ?, ?)",
            (order_id, line["name"], line["quantity"], line["unit_price_cents"]),
        )
        connection.execute(
            "UPDATE products SET stock = stock - ? WHERE name = ? AND stock >= ?",
            (line["quantity"], line["name"], line["quantity"]),
        )
    connection.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
    connection.commit()
    return reference


def order_by_reference(user_id: int, reference: str):
    rows = db.query(
        "SELECT id, reference, total_cents, status, ship_name, placed_at"
        " FROM orders WHERE reference = ? AND user_id = ?",
        (reference, user_id),
    )
    return rows[0] if rows else None


def order_lines(order_id: int) -> list[dict]:
    rows = db.query(
        "SELECT name, quantity, unit_price_cents FROM order_items"
        " WHERE order_id = ? ORDER BY id",
        (order_id,),
    )
    return [
        {
            "name": row["name"],
            "quantity": row["quantity"],
            "unit_price_cents": row["unit_price_cents"],
            "line_total_cents": row["quantity"] * row["unit_price_cents"],
        }
        for row in rows
    ]
