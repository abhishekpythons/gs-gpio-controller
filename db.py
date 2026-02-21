import sqlite3
from datetime import datetime

DB = "tarang.db"

def init_db():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            pin INTEGER,
            state TEXT,
            timestamp TEXT
        )
        """)

def log_action(username, action, pin=None, state=None):
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO logs VALUES (NULL,?,?,?,?,?)",
            (username, action, pin, state, datetime.utcnow().isoformat())
        )

def get_logs(limit=50):
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(r) for r in cur.fetchall()]
