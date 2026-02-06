import json

DATA_PATH = "data/users.json"

def load_data():
    """Load all users from the JSON file. Returns dict of {username: user_data}"""
    try:
        with open(DATA_PATH, "r") as f:
            data = json.load(f)
            # If it's in old format (single user), convert to multi-user format
            if "username" in data and not isinstance(data.get("username"), dict):
                return {data["username"]: data}
            return data
    except FileNotFoundError:
        return {}

def save_data(users_dict):
    """Save all users to the JSON file. Expects dict of {username: user_data}"""
    with open(DATA_PATH, "w") as f:
        json.dump(users_dict, f, indent=2)

def load_user(username):
    """Load a specific user's data. Returns user dict or None if not found."""
    users = load_data()
    return users.get(username)

def save_user(username, user_data):
    """Save a specific user's data."""
    users = load_data()
    users[username] = user_data
    save_data(users)
