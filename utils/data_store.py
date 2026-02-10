import json
import os
import sqlite3
import requests

# Detect environment
IS_VERCEL = os.environ.get("VERCEL") == "1"

# Edge Config credentials (on Vercel)
EDGE_CONFIG_URL = os.environ.get("EDGE_CONFIG")

# Extract token from URL if embedded, otherwise use env var
EDGE_CONFIG_TOKEN = None
if EDGE_CONFIG_URL and "token=" in EDGE_CONFIG_URL:
    # Token is embedded in URL like /xxx/token=yyy
    EDGE_CONFIG_TOKEN = EDGE_CONFIG_URL.split("token=")[1].split("&")[0]
    # Remove token from URL for clean API calls
    EDGE_CONFIG_URL = EDGE_CONFIG_URL.split("?token=")[0].split("&token=")[0]
else:
    # Token is in a separate env var
    EDGE_CONFIG_TOKEN = os.environ.get("smart_dashboard-token")

# Normalize EDGE_CONFIG_URL: remove trailing /items and trailing slash
if EDGE_CONFIG_URL:
    EDGE_CONFIG_URL = EDGE_CONFIG_URL.rstrip('/')
    if EDGE_CONFIG_URL.endswith('/items'):
        EDGE_CONFIG_URL = EDGE_CONFIG_URL[:-len('/items')]

# SQLite database (local only)
SQLITE_DB = "data/smart_dashboard.db"
JSON_SOURCE_PATH = "data/users.json"


def _get_sqlite_conn():
    """Get SQLite connection."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _init_sqlite_db():
    """Initialize SQLite schema."""
    conn = _get_sqlite_conn()
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            date TEXT,
            amount REAL,
            category TEXT,
            merchant TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)
    
    conn.commit()
    conn.close()


def _migrate_json_to_sqlite_if_needed():
    """Migrate data from JSON to SQLite on first run."""
    conn = _get_sqlite_conn()
    cur = conn.cursor()
    
    # Check if DB already has data
    cur.execute("SELECT COUNT(*) as c FROM users")
    if cur.fetchone()[0] > 0:
        conn.close()
        return
    
    # Try to load from JSON source
    if not os.path.exists(JSON_SOURCE_PATH):
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
                "INSERT INTO users (username, password, profile, accounts, chat_history) VALUES (?, ?, ?, ?, ?)",
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
                    "INSERT INTO transactions (username, date, amount, category, merchant) VALUES (?, ?, ?, ?, ?)",
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
        conn.close()


def _edge_config_get():
    """Fetch data from Vercel Edge Config."""
    if not EDGE_CONFIG_URL or not EDGE_CONFIG_TOKEN:
        print("WARNING: EDGE_CONFIG_URL or EDGE_CONFIG_TOKEN not set")
        return {}
    
    try:
        url = f"{EDGE_CONFIG_URL}/items?key=app_data&token={EDGE_CONFIG_TOKEN}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result = json.loads(data.get("items", [{}])[0].get("value", "{}"))
            print(f"Edge Config read: got {len(result)} users")
            return result
        print(f"Edge Config read failed: {resp.status_code}")
        return {}
    except Exception as e:
        print(f"Edge Config read error: {e}")
        return {}


def _edge_config_set(data):
    """Save data to Vercel Edge Config."""
    if not EDGE_CONFIG_URL or not EDGE_CONFIG_TOKEN:
        print("WARNING: EDGE_CONFIG_URL or EDGE_CONFIG_TOKEN not set")
        print(f"  EDGE_CONFIG_URL={EDGE_CONFIG_URL}")
        print(f"  EDGE_CONFIG_TOKEN={'*' * 10 if EDGE_CONFIG_TOKEN else 'None'}")
        return
    
    try:
        payload = {
            "items": [
                {
                    "key": "app_data",
                    "value": json.dumps(data)
                }
            ]
        }
        url = f"{EDGE_CONFIG_URL}/items?token={EDGE_CONFIG_TOKEN}"
        print(f"Edge Config write: PATCH to {EDGE_CONFIG_URL}/items?token=***")
        resp = requests.patch(url, json=payload, timeout=10)
        
        if resp.status_code not in [200, 204]:
            print(f"Edge Config write failed: {resp.status_code} - {resp.text}")
        else:
            print(f"Edge Config updated: {len(data)} users saved")
            
    except Exception as e:
        print(f"Edge Config write error: {e}")


def load_data():
    """Load all users from SQLite (local) or Edge Config (Vercel)."""
    if IS_VERCEL:
        print("Loading from Edge Config...")
        data = _edge_config_get()
        
        # If Edge Config is empty, initialize from JSON
        if not data and os.path.exists(JSON_SOURCE_PATH):
            print("Edge Config empty, initializing from JSON...")
            try:
                with open(JSON_SOURCE_PATH, "r") as f:
                    json_data = json.load(f)
                
                # Handle old single-user format
                if "username" in json_data and not isinstance(json_data.get("username"), dict):
                    data = {json_data["username"]: json_data}
                else:
                    data = json_data
                
                print(f"Loaded {len(data)} users from JSON, saving to Edge Config...")
                # Save to Edge Config
                _edge_config_set(data)
            except Exception as e:
                print(f"Error initializing Edge Config from JSON: {e}")
        
        return data
    
    # Local: use SQLite
    _init_sqlite_db()
    _migrate_json_to_sqlite_if_needed()
    
    conn = _get_sqlite_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT username, password, profile, accounts, chat_history FROM users")
    users_dict = {}
    
    for row in cur.fetchall():
        username = row["username"]
        
        # Get transactions for this user
        cur.execute(
            "SELECT date, amount, category, merchant FROM transactions WHERE username = ? ORDER BY id",
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
    
    conn.close()
    return users_dict


def save_data(users_dict):
    """Save all users to SQLite (local) or Edge Config (Vercel)."""
    if IS_VERCEL:
        _edge_config_set(users_dict)
        return
    
    # Local: use SQLite
    _init_sqlite_db()
    conn = _get_sqlite_conn()
    cur = conn.cursor()
    
    try:
        # Clear existing data
        cur.execute("DELETE FROM transactions")
        cur.execute("DELETE FROM users")
        
        # Insert all users and their transactions
        for username, user_data in users_dict.items():
            cur.execute(
                "INSERT INTO users (username, password, profile, accounts, chat_history) VALUES (?, ?, ?, ?, ?)",
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
                    "INSERT INTO transactions (username, date, amount, category, merchant) VALUES (?, ?, ?, ?, ?)",
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
    Save a single user.
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