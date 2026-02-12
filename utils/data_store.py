import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Detect environment
IS_VERCEL = os.environ.get("VERCEL") == "1"

# Database connection URL
DATABASE_URL = os.environ.get("DATABASE_URL")

# Fallback paths for local development
JSON_SOURCE_PATH = "data/users.json"


def get_db_conn():
    """Get Postgres connection."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")
    
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise


def init_db():
    """Initialize Postgres database schema."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                profile JSONB DEFAULT '{}',
                accounts JSONB DEFAULT '{}',
                chat_history JSONB DEFAULT '[]'
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                username TEXT REFERENCES users(username) ON DELETE CASCADE,
                date TEXT,
                amount REAL,
                category TEXT,
                merchant TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for better query performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_username 
            ON transactions(username)
        """)
        
        conn.commit()
        print("Database schema initialized successfully")
    except Exception as e:
        conn.rollback()
        print(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()


def migrate_json_to_postgres_if_needed():
    """Migrate data from JSON to Postgres on first run."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Check if DB already has data
        cur.execute("SELECT COUNT(*) as count FROM users")
        result = cur.fetchone()
        if result['count'] > 0:
            conn.close()
            return
        
        # Try to load from JSON source
        if not os.path.exists(JSON_SOURCE_PATH):
            conn.close()
            return
        
        print("Migrating data from JSON to Postgres...")
        
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
                """
                INSERT INTO users (username, password, profile, accounts, chat_history) 
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                """,
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
                    """
                    INSERT INTO transactions (username, date, amount, category, merchant) 
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        username,
                        tx.get("date"),
                        tx.get("amount"),
                        tx.get("category"),
                        tx.get("merchant")
                    )
                )
        
        conn.commit()
        print(f"Successfully migrated {len(users_dict)} users to Postgres")
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()


def load_data():
    """Load all users from Postgres."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT username, password, profile, accounts, chat_history 
            FROM users
        """)
        
        users_dict = {}
        
        for row in cur.fetchall():
            username = row["username"]
            
            # Get transactions for this user
            cur.execute(
                """
                SELECT date, amount, category, merchant 
                FROM transactions 
                WHERE username = %s 
                ORDER BY id
                """,
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
                "profile": row["profile"] if isinstance(row["profile"], dict) else {},
                "accounts": row["accounts"] if isinstance(row["accounts"], dict) else {},
                "transactions": transactions,
                "chat_history": row["chat_history"] if isinstance(row["chat_history"], list) else []
            }
        
        return users_dict
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}
    finally:
        conn.close()


def save_data(users_dict):
    """Save all users to Postgres."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Clear existing data
        cur.execute("DELETE FROM transactions")
        cur.execute("DELETE FROM users")
        
        # Insert all users and their transactions
        for username, user_data in users_dict.items():
            cur.execute(
                """
                INSERT INTO users (username, password, profile, accounts, chat_history) 
                VALUES (%s, %s, %s, %s, %s)
                """,
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
                    """
                    INSERT INTO transactions (username, date, amount, category, merchant) 
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        username,
                        tx.get("date"),
                        tx.get("amount"),
                        tx.get("category"),
                        tx.get("merchant")
                    )
                )
        
        conn.commit()
        print(f"Successfully saved {len(users_dict)} users to Postgres")
    except Exception as e:
        print(f"Save error: {e}")
        conn.rollback()
        raise
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


# Initialize database on import
if DATABASE_URL:
    try:
        init_db()
        migrate_json_to_postgres_if_needed()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")