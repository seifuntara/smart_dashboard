import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# PostgreSQL connection
DATABASE_URL = os.environ.get("DATABASE_URL")

# For local development, use environment variable or default
if not DATABASE_URL:
    DATABASE_URL = os.environ.get("DATABASE_LOCAL_URL", "postgresql://postgres:postgres@localhost/smart_dashboard")

JSON_SOURCE_PATH = "data/users.json"


def _get_conn():
    """Get PostgreSQL connection."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def _init_db():
    """Initialize database schema."""
    conn = _get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            profile TEXT,
            accounts TEXT,
            chat_history TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            username TEXT,
            date TEXT,
            amount REAL,
            category TEXT,
            merchant TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()


def _migrate_json_to_db_if_needed():
    """Migrate data from JSON to PostgreSQL on first run."""
    conn = _get_conn()
    cur = conn.cursor()
    
    # Check if DB already has data
    cur.execute("SELECT COUNT(*) as c FROM users")
    if cur.fetchone()[0] > 0:
        cur.close()
        conn.close()
        return
    
    # Try to load from JSON source
    if not os.path.exists(JSON_SOURCE_PATH):
        cur.close()
        conn.close()
        return
    
    try:
        with open(JSON_SOURCE_PATH, "r") as f:
            json_data = json.load(f)
        
        # Handle old single-user format
        if "username" in json_data and not isinstance(json_data.get("username"), dict):
            users_dict = {json_data["username"]: json_data}
        else:
            users_dict = json_data
        
        # Insert into DB
        for username, user_data in users_dict.items():
            cur.execute(
                "INSERT INTO users (username, password, profile, accounts, chat_history) VALUES (%s, %s, %s, %s, %s)",
                (
                    username,
                    user_data.get("password"),
                    json.dumps(user_data.get("profile", {})),
                    json.dumps(user_data.get("accounts", {})),
                    json.dumps(user_data.get("chat_history", []))
                )
            )
            
            for tx in user_data.get("transactions", []):
                cur.execute(
                    "INSERT INTO transactions (username, date, amount, category, merchant) VALUES (%s, %s, %s, %s, %s)",
                    (
                        username,
                        tx.get("date"),
                        tx.get("amount"),
                        tx.get("category"),
                        tx.get("merchant")
                    )
                )
        
        conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def load_data():
    """Load all users from PostgreSQL."""
    _init_db()
    _migrate_json_to_db_if_needed()
    
    conn = _get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT username, password, profile, accounts, chat_history FROM users")
    users_dict = {}
    
    for row in cur.fetchall():
        username = row["username"]
        
        # Get transactions for this user
        cur.execute(
            "SELECT date, amount, category, merchant FROM transactions WHERE username = %s ORDER BY id",
            (username,)
        )
        transactions = [
            {
                "date": r["date"],
                "amount": r["amount"],
                "category": r["category"],
                "merchant": r["merchant"]
            }
            for r in cur.fetchall()
        ]
        
        users_dict[username] = {
            "username": username,
            "password": row["password"],
            "profile": json.loads(row["profile"] or "{}"),
            "accounts": json.loads(row["accounts"] or "{}"),
            "transactions": transactions,
            "chat_history": json.loads(row["chat_history"] or "[]")
        }
    
    cur.close()
    conn.close()
    return users_dict


def save_data(users_dict):
    """Save all users to PostgreSQL."""
    _init_db()
    conn = _get_conn()
    cur = conn.cursor()
    
    try:
        # Clear existing data
        cur.execute("DELETE FROM transactions")
        cur.execute("DELETE FROM users")
        
        # Insert all users and their transactions
        for username, user_data in users_dict.items():
            cur.execute(
                "INSERT INTO users (username, password, profile, accounts, chat_history) VALUES (%s, %s, %s, %s, %s)",
                (
                    username,
                    user_data.get("password"),
                    json.dumps(user_data.get("profile", {})),
                    json.dumps(user_data.get("accounts", {})),
                    json.dumps(user_data.get("chat_history", []))
                )
            )
            
            for tx in user_data.get("transactions", []):
                cur.execute(
                    "INSERT INTO transactions (username, date, amount, category, merchant) VALUES (%s, %s, %s, %s, %s)",
                    (
                        username,
                        tx.get("date"),
                        tx.get("amount"),
                        tx.get("category"),
                        tx.get("merchant")
                    )
                )
        
        conn.commit()
    except Exception as e:
        print(f"Save error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def load_user(username=None):
    """Load a specific user by username, or first user if no username provided."""
    data = load_data()
    
    if username:
        return data.get(username)
    
    # Fallback: return first user
    if data:
        return list(data.values())[0]
    return None


def save_user(username_or_data, user_data=None):
    """
    Save a single user to SQLite.
    Can be called as:
    - save_user(user_dict) where user_dict contains 'username' key
    - save_user(username, user_dict)
    """
    data = load_data()
    
    if user_data is None:
        # Called with single arg: save_user(user_dict)
        user_dict = username_or_data
        username = user_dict.get("username")
    else:
        # Called with two args: save_user(username, user_dict)
        username = username_or_data
        user_dict = user_data
    
    if username:
        data[username] = user_dict
        save_data(data)