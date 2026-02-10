import json
import os
import sqlite3

JSON_PATH = "data/users.json"
DB_PATH = "data/users.db"


def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            profile TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date TEXT,
            amount REAL,
            category TEXT,
            merchant TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def _migrate_json_if_needed():
    # If DB already has a user, skip migration
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) as c FROM users")
    row = cur.fetchone()
    if row and row["c"] > 0:
        conn.close()
        return

    # If JSON exists, load and insert into DB
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r") as f:
                data = json.load(f)

            cur.execute(
                "INSERT INTO users (username, password, profile) VALUES (?, ?, ?)",
                (data.get("username"), data.get("password"), json.dumps(data.get("profile", {})))
            )
            user_id = cur.lastrowid

            for t in data.get("transactions", []):
                cur.execute(
                    "INSERT INTO transactions (user_id, date, amount, category, merchant) VALUES (?, ?, ?, ?, ?)",
                    (user_id, t.get("date"), float(t.get("amount", 0)), t.get("category"), t.get("merchant", ""))
                )

            conn.commit()
        except Exception:
            # If migration fails, don't crash — leave DB empty
            pass

    conn.close()


def load_user():
    _init_db()
    _migrate_json_if_needed()

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id LIMIT 1")
    row = cur.fetchone()
    if not row:
        conn.close()
        return {}

    user_id = row["id"]
    username = row["username"]
    password = row["password"]
    profile = json.loads(row["profile"] or "{}")

    cur.execute("SELECT date, amount, category, merchant FROM transactions WHERE user_id = ? ORDER BY id", (user_id,))
    tx_rows = cur.fetchall()
    transactions = []
    for r in tx_rows:
        transactions.append({
            "date": r["date"],
            "amount": r["amount"],
            "category": r["category"],
            "merchant": r["merchant"]
        })

    conn.close()

    return {
        "username": username,
        "password": password,
        "profile": profile,
        "transactions": transactions,
    }


def save_user(data):
    # Upsert single user and replace transactions for that user
    _init_db()
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users ORDER BY id LIMIT 1")
    row = cur.fetchone()

    profile_json = json.dumps(data.get("profile", {}))

    if row:
        user_id = row["id"]
        cur.execute(
            "UPDATE users SET username = ?, password = ?, profile = ? WHERE id = ?",
            (data.get("username"), data.get("password"), profile_json, user_id)
        )
    else:
        cur.execute(
            "INSERT INTO users (username, password, profile) VALUES (?, ?, ?)",
            (data.get("username"), data.get("password"), profile_json)
        )
        user_id = cur.lastrowid

    # Replace transactions
    cur.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    for t in data.get("transactions", []):
        cur.execute(
            "INSERT INTO transactions (user_id, date, amount, category, merchant) VALUES (?, ?, ?, ?, ?)",
            (user_id, t.get("date"), float(t.get("amount", 0)), t.get("category"), t.get("merchant", ""))
        )

    conn.commit()
    conn.close()
