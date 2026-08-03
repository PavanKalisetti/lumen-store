from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from app import markers
from app.config import Config
from app.store import attachments
from app.views.auth import login_required

bp = Blueprint("support", __name__, url_prefix="/support")

PARTNER_KEY = os.path.join(Config.ASSET_DIR, "fulfilment", "partner_key.txt")


def seed_partner_key() -> None:
    target = Path(PARTNER_KEY)
    expected = (markers.value("ticket") + "\n").encode("utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.read_bytes() != expected:
        target.write_bytes(expected)


def issue_upload_token(ticket_id: int) -> str:
    tokens = dict(session.get("upload_tokens") or {})
    token = secrets.token_urlsafe(16)
    tokens[str(ticket_id)] = token
    session["upload_tokens"] = tokens
    return token


def consume_upload_token(ticket_id: int, supplied: str) -> bool:
    tokens = dict(session.get("upload_tokens") or {})
    expected = tokens.get(str(ticket_id))
    if not expected or not supplied:
        return False
    if not secrets.compare_digest(expected, supplied):
        return False
    tokens.pop(str(ticket_id), None)
    session["upload_tokens"] = tokens
    return True


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new_ticket():
    seed_partner_key()
    recent = attachments.user_tickets(session["user_id"])
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()
        if not subject or not body:
            return render_template(
                "support/new.html",
                recent=recent,
                subject=subject,
                body=body,
                error="Give the ticket a subject and a short description.",
            )
        ticket_id = attachments.create_ticket(session["user_id"], subject, body)
        issue_upload_token(ticket_id)
        return redirect(url_for("support.ticket", ticket_id=ticket_id))
    return render_template("support/new.html", recent=recent)


@bp.post("/tickets/<int:ticket_id>/attachments")
@login_required
def add_attachment(ticket_id: int):
    if attachments.load_ticket(ticket_id, session["user_id"]) is None:
        abort(404)
    if not consume_upload_token(ticket_id, request.form.get("upload_token", "")):
        abort(400)
    upload = request.files.get("attachment")
    if upload is None or not upload.filename:
        abort(400)
    attachments.store_attachment(ticket_id, upload.filename, upload.stream)
    return redirect(url_for("support.ticket", ticket_id=ticket_id))


@bp.get("/tickets/<int:ticket_id>")
@login_required
def ticket(ticket_id: int):
    row = attachments.load_ticket(ticket_id, session["user_id"])
    if row is None:
        abort(404)
    preview = attachments.read_attachment(ticket_id)
    token = (session.get("upload_tokens") or {}).get(str(ticket_id))
    return render_template(
        "support/ticket.html",
        ticket=row,
        preview=preview,
        upload_token=token,
    )
