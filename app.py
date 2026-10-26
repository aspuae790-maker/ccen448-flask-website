"""CCEN448 Exercise 6: Dynamic Flask website."""

import os
import sqlite3
from functools import wraps

from flask import Flask, redirect, render_template_string, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "local-development-only")
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>CCEN448 Dynamic Website</title>
    <style>
        body { font-family: Arial; background: #eef2f7; text-align: center; padding: 50px; }
        .card { background: white; padding: 30px; max-width: 400px; margin: auto;
                border-radius: 12px; box-shadow: 0 3px 12px #ccc; }
        input, button { padding: 12px; margin: 8px; width: 85%; }
        button { background: #2563eb; color: white; border: none; cursor: pointer; }
        a { color: #2563eb; }
        .error { color: red; }
    </style>
</head>
<body>
<div class="card">
    <h1>CCEN448 Dynamic Website</h1>
    <p>{{ message }}</p>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}

    {% if username %}
        <h2>Welcome, {{ username }}!</h2>
        <p>You have successfully logged in.</p>
        <a href="/logout">Logout</a>
    {% else %}
        <form method="POST" action="{{ action }}">
            <input name="username" placeholder="Username" required>
            <input name="password" type="password" placeholder="Password" required>
            <button type="submit">{{ button }}</button>
        </form>
        <p><a href="/login">Login</a> | <a href="/register">Register</a></p>
    {% endif %}
</div>
</body>
</html>
"""


def get_db():
    """Open a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create the users table if it does not exist."""
    with get_db() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS users "
            "(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)"
        )


@app.route("/")
def home():
    """Display the homepage."""
    return render_template_string(
        PAGE,
        username=session.get("username"),
        message="Hosted using AWS Lightsail and OpenTofu",
        error=None,
        action="/login",
        button="Login"
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user."""
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            error = "Username and password are required."
        else:
            try:
                with get_db() as db:
                    db.execute(
                        "INSERT INTO users (username, password) VALUES (?, ?)",
                        (username, generate_password_hash(password))
                    )
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "Username already exists."

    return render_template_string(
        PAGE, username=None, message="Create an account",
        error=error, action="/register", button="Register"
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a registered user."""
    error = None
    if request.method == "POST":
        with get_db() as db:
            user = db.execute(
                "SELECT password FROM users WHERE username = ?",
                (request.form["username"],)
            ).fetchone()

        if user and check_password_hash(user[0], request.form["password"]):
            session["username"] = request.form["username"]
            return redirect(url_for("home"))
        error = "Invalid username or password."

    return render_template_string(
        PAGE, username=None, message="Login to your account",
        error=error, action="/login", button="Login"
    )


@app.route("/logout")
def logout():
    """Log out the current user."""
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000)
