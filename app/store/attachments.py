from __future__ import annotations

import os
import sqlite3
from datetime import date
from pathlib import Path

from app import db
from app.config import Config


def create_ticket(user_id: int, subject: str, body: str) -> int:
    connection = db.connect()
    cursor = connection.execute(
        "INSERT INTO tickets (user_id, subject, body, opened_at) VALUES (?, ?, ?, ?)",
        (user_id, subject, body, date.today().isoformat()),
    )
    connection.commit()
    ticket_id = cursor.lastrowid
    cursor.close()
    return int(ticket_id)


def load_ticket(ticket_id: int, user_id: int) -> sqlite3.Row | None:
    rows = db.query(
        "SELECT id, subject, body, attachment, opened_at FROM tickets"
        " WHERE id = ? AND user_id = ?",
        (ticket_id, user_id),
    )
    return rows[0] if rows else None


def user_tickets(user_id: int) -> list[sqlite3.Row]:
    return db.query(
        "SELECT id, subject, opened_at FROM tickets WHERE user_id = ?"
        " ORDER BY id DESC LIMIT 8",
        (user_id,),
    )


def store_attachment(ticket_id: int, filename: str, stream) -> str:
    destination = os.path.join(Config.UPLOAD_DIR, filename)
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "wb") as handle:
        handle.write(stream.read())

    connection = db.connect()
    connection.execute(
        "UPDATE tickets SET attachment = ? WHERE id = ?",
        (filename, ticket_id),
    )
    connection.commit()
    return filename


def read_attachment(ticket_id: int) -> str:
    rows = db.query("SELECT attachment FROM tickets WHERE id = ?", (ticket_id,))
    if not rows:
        return ""
    stored_name = rows[0]["attachment"]
    if not stored_name:
        return ""
    source = os.path.join(Config.UPLOAD_DIR, stored_name)
    try:
        with open(source, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(20000)
    except OSError:
        return ""
