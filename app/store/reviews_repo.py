from __future__ import annotations

import sqlite3

from app import db


def find_product(slug: str) -> sqlite3.Row | None:
    rows = db.query(
        "SELECT id, slug, name, price_cents, stock, summary, description"
        " FROM products WHERE slug = ?",
        (slug,),
    )
    return rows[0] if rows else None


def add_review(product_id: int, author: str, rating: int, body: str) -> int:
    connection = db.connect()
    cursor = connection.execute(
        "INSERT INTO reviews (product_id, author, rating, body) VALUES (?, ?, ?, ?)",
        (product_id, author, rating, body),
    )
    review_id = cursor.lastrowid
    cursor.close()
    connection.commit()
    return review_id


def average_rating(product_id: int) -> float:
    rows = db.query(
        "SELECT AVG(rating) AS score FROM reviews WHERE product_id = ?",
        (product_id,),
    )
    score = rows[0]["score"] if rows else None
    return round(score, 1) if score is not None else 0.0


def render_payload(product_id: int) -> dict:
    connection = db.connect()
    cursor = connection.execute(
        "SELECT name FROM products WHERE id = ?",
        (product_id,),
    )
    product = cursor.fetchone()
    cursor.close()

    rows = db.query(
        "SELECT author, rating, body FROM reviews WHERE product_id = ? ORDER BY id DESC",
        (product_id,),
    )

    html_fragments = []
    for row in rows:
        html_fragments.append(
            '<div class="review">'
            f"<p>{row['body']}</p>"
            f'<p class="byline">{row["author"]} · {row["rating"]} of 5</p>'
            "</div>"
        )

    return {
        "count": len(rows),
        "product": product["name"] if product else "",
        "average": average_rating(product_id),
        "html_fragments": html_fragments,
    }
