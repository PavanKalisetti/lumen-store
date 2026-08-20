from __future__ import annotations

import secrets
from functools import wraps

from flask import (
    Blueprint,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app import db

bp = Blueprint("auth", __name__)


def form_token() -> str:
    if "form_token" not in session:
        session["form_token"] = secrets.token_urlsafe(24)
    return session["form_token"]


def require_login() -> Response | None:
    """Guard helper: returns a redirect when the caller has no session, else None."""
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    return None


def login_required(view):
    """Decorator form of :func:`require_login` for whole view functions."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        guard = require_login()
        if guard is not None:
            return guard
        return view(*args, **kwargs)

    return wrapper


def authenticate(email: str, password: str):
    connection = db.connect()
    cursor = connection.execute(
        "SELECT id, email, role, display_name FROM users"
        " WHERE email = ? AND password = ?",
        (email, password),
    )
    row = cursor.fetchone()
    cursor.close()
    return row


def email_taken(email: str) -> bool:
    connection = db.connect()
    cursor = connection.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    cursor.close()
    return row is not None


def create_account(email: str, password: str, display_name: str) -> int:
    connection = db.connect()
    cursor = connection.execute(
        "INSERT INTO users (email, password, role, display_name)"
        " VALUES (?, ?, 'customer', ?)",
        (email, password, display_name),
    )
    user_id = cursor.lastrowid
    cursor.close()
    connection.commit()
    return user_id


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        submitted = request.form.get("form_token", "")
        expected = session.get("form_token")
        if not expected or not secrets.compare_digest(submitted, expected):
            error = "That form expired. Please try again."
        else:
            user = authenticate(email, password)
            if user is None:
                error = "We could not match that email and password."
            else:
                session["user_id"] = user["id"]
                session["display_name"] = user["display_name"]
                session["role"] = user["role"]
                return redirect(url_for("catalog.index"))
    return render_template("auth/login.html", error=error, email=email, token=form_token())


@bp.route("/register", methods=["GET", "POST"])
def register():
    error = None
    email = ""
    display_name = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")
        submitted = request.form.get("form_token", "")
        expected = session.get("form_token")
        if not expected or not secrets.compare_digest(submitted, expected):
            error = "That form expired. Please try again."
        elif "@" not in email:
            error = "Enter an email address we can send receipts to."
        elif len(password) < 8:
            error = "Passwords need at least 8 characters."
        elif email_taken(email):
            error = "That email already has an account."
        else:
            name = display_name or email.split("@")[0]
            session["user_id"] = create_account(email, password, name)
            session["display_name"] = name
            session["role"] = "customer"
            return redirect(url_for("catalog.index"))
    return render_template(
        "auth/register.html",
        error=error,
        email=email,
        display_name=display_name,
        token=form_token(),
    )


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("catalog.index"))
