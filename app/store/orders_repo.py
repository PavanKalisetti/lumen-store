from __future__ import annotations

import sqlite3

from app import db


def list_for_user(user_id: int) -> list[sqlite3.Row]:
    return db.query(
        "SELECT id, reference, total_cents, status, placed_at FROM orders"
        " WHERE orders.user_id = ? ORDER BY orders.id DESC",
        (user_id,),
    )


def find_by_reference(reference: str) -> dict | None:
    connection = db.connect()
    cursor = connection.execute(
        "SELECT id, user_id, reference, total_cents, status, ship_name, ship_address,"
        " placed_at FROM orders WHERE reference = ?",
        (reference,),
    )
    order = cursor.fetchone()
    cursor.close()
    if order is None:
        return None
    items = db.query(
        "SELECT name, quantity, unit_price_cents FROM order_items"
        " WHERE order_id = ? ORDER BY id",
        (order["id"],),
    )
    return {"order": order, "items": items}
