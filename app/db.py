from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import current_app, g

from app import markers

SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer',
    display_name TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT ''
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    summary TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    rating INTEGER NOT NULL DEFAULT 5,
    body TEXT NOT NULL DEFAULT ''
);

CREATE TABLE cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price_cents INTEGER NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    reference TEXT NOT NULL UNIQUE,
    total_cents INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'placed',
    ship_name TEXT NOT NULL DEFAULT '',
    ship_address TEXT NOT NULL DEFAULT '',
    placed_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price_cents INTEGER NOT NULL
);

CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subject TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    attachment TEXT NOT NULL DEFAULT '',
    opened_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE supplier_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier TEXT NOT NULL,
    contract_note TEXT NOT NULL DEFAULT ''
);

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
"""

USERS = (
    ("dana@lumensupply.co", "GreenKettle41", "staff", "Dana Whitfield", "+1-503-555-0142"),
    ("marcus@northgate.example", "Rosewood7Loom", "customer", "Marcus Ellery", "+1-503-555-0188"),
    ("priya@fernvale.example", "Cobalt9Anchor", "customer", "Priya Raghunath", "+1-503-555-0164"),
)

PRODUCTS = (
    ("cedar-desk-lamp", "Cedar Desk Lamp", 8400, 24, "Warm brass shade on a cedar base.",
     "A compact task lamp with a solid cedar base and a hand-finished brass shade."),
    ("linen-apron", "Linen Work Apron", 5200, 40, "Heavyweight flax with leather ties.",
     "Cut from heavyweight European flax and finished with vegetable-tanned leather ties."),
    ("stoneware-mug", "Stoneware Mug", 2200, 120, "Reactive glaze, 12oz.",
     "Thrown in small batches and finished with a reactive glaze, so no two are identical."),
    ("walnut-tray", "Walnut Serving Tray", 9600, 12, "Oiled walnut with routed handles.",
     "Milled from a single walnut board and finished with a food-safe hardwood oil."),
    ("canvas-tote", "Waxed Canvas Tote", 6800, 33, "18oz waxed canvas, brass hardware.",
     "An everyday carry built from 18oz waxed canvas with solid brass hardware."),
)

REVIEWS = (
    ("cedar-desk-lamp", "Marcus E.", 5, "Brighter than I expected and the base feels substantial."),
    ("cedar-desk-lamp", "Priya R.", 4, "Lovely finish. Cable is a little short for my desk."),
    ("linen-apron", "Marcus E.", 5, "Holds up well after a dozen washes."),
    ("stoneware-mug", "Priya R.", 5, "The glaze pattern on mine came out beautifully."),
    ("walnut-tray", "Marcus E.", 4, "Grain is gorgeous. Slightly heavier than I pictured."),
)

ORDERS = (
    ("marcus@northgate.example", "LM-4417-QD", 13600, "shipped", "Marcus Ellery",
     "1184 Alder Court, Apt 3, Portland OR 97214", "2026-06-14",
     (("Cedar Desk Lamp", 1, 8400), ("Linen Work Apron", 1, 5200))),
    ("priya@fernvale.example", "LM-4482-HV", 11800, "packing", "Priya Raghunath",
     "77 Fernvale Terrace, Beaverton OR 97005", "2026-07-02",
     (("Waxed Canvas Tote", 1, 6800), ("Stoneware Mug", 2, 2200), ("Cedar Desk Lamp", 0, 0))),
)


def connect() -> sqlite3.Connection:
    if "connection" not in g:
        g.connection = sqlite3.connect(current_app.config["DATABASE"])
        g.connection.row_factory = sqlite3.Row
    return g.connection


def close(_exception: object = None) -> None:
    connection = g.pop("connection", None)
    if connection is not None:
        connection.close()


def query(statement: str, parameters: tuple = ()) -> list[sqlite3.Row]:
    cursor = connect().execute(statement, parameters)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def build(app) -> None:
    target = Path(app.config["DATABASE"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    Path(app.config["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["ASSET_DIR"]).mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(target))
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)

    for email, password, role, display_name, phone in USERS:
        connection.execute(
            "INSERT INTO users (email, password, role, display_name, phone)"
            " VALUES (?, ?, ?, ?, ?)",
            (email, password, role, display_name, phone),
        )
    for slug, name, price, stock, summary, description in PRODUCTS:
        connection.execute(
            "INSERT INTO products (slug, name, price_cents, stock, summary, description)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (slug, name, price, stock, summary, description),
        )
    for slug, author, rating, body in REVIEWS:
        product = connection.execute(
            "SELECT id FROM products WHERE slug = ?", (slug,)
        ).fetchone()
        connection.execute(
            "INSERT INTO reviews (product_id, author, rating, body) VALUES (?, ?, ?, ?)",
            (product["id"], author, rating, body),
        )
    for email, reference, total, status, ship_name, ship_address, placed_at, items in ORDERS:
        user = connection.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        cursor = connection.execute(
            "INSERT INTO orders (user_id, reference, total_cents, status, ship_name,"
            " ship_address, placed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user["id"], reference, total, status, ship_name, ship_address, placed_at),
        )
        for name, quantity, unit_price in items:
            if quantity == 0:
                continue
            connection.execute(
                "INSERT INTO order_items (order_id, name, quantity, unit_price_cents)"
                " VALUES (?, ?, ?, ?)",
                (cursor.lastrowid, name, quantity, unit_price),
            )

    connection.execute(
        "INSERT INTO supplier_notes (supplier, contract_note) VALUES (?, ?)",
        ("Alder & Vine Woodworks", "Net-30 terms renewed through Q4."),
    )
    connection.execute(
        "INSERT INTO supplier_notes (supplier, contract_note) VALUES (?, ?)",
        ("Fernvale Textiles", f"Rebate reference {markers.value('catalog')}"),
    )
    connection.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?)",
        ("store_name", "Lumen Supply Co."),
    )
    connection.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?)",
        ("support_email", "help@lumensupply.co"),
    )
    connection.commit()
    connection.close()
