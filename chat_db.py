# chat_db.py
import sqlite3
import json
from datetime import datetime
import bcrypt  # used only for hashing helper if needed

DB_FILE = "chat_history.db"

def _conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = _conn()
    c = conn.cursor()
    # users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # messages table
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ---------- User functions ----------
def create_user(username: str, password_hash: str, name: str = "") -> bool:
    conn = _conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
                  (username, password_hash, name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username: str):
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash, name FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row  # (id, username, password_hash, name) or None

# ---------- Auth helpers ----------
def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode(), password_hash.encode())
    except Exception:
        return False

# ---------- Messages ----------
def save_message(username: str, role: str, content: str):
    conn = _conn()
    c = conn.cursor()
    c.execute("INSERT INTO messages (username, role, content) VALUES (?, ?, ?)",
              (username, role, content))
    conn.commit()
    conn.close()

def get_messages_for_user(username: str):
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT id, role, content, timestamp FROM messages WHERE username=? ORDER BY id ASC", (username,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "role": r[1], "content": r[2], "timestamp": r[3]} for r in rows]

def delete_message_by_id(message_id: int, username: str):
    conn = _conn()
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE id=? AND username=?", (message_id, username))
    conn.commit()
    conn.close()

def clear_history(username: str):
    conn = _conn()
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE username=?", (username,))
    conn.commit()
    conn.close()
