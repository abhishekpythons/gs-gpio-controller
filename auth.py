import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from db import DB

def create_user(username, password):
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO users VALUES (?,?)",
            (username, generate_password_hash(password))
        )

def verify_user(username, password):
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("SELECT password FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        return row and check_password_hash(row[0], password)
