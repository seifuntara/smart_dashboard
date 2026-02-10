import json
import os

# Use /tmp on Vercel (writable), otherwise use data/users.json
if os.environ.get("VERCEL"):
    JSON_PATH = "/tmp/users.json"
else:
    JSON_PATH = "data/users.json"


def load_data():
    """Load all users from the JSON file."""
    if not os.path.exists(JSON_PATH):
        return {}
    
    with open(JSON_PATH, "r") as f:
        try:
            data = json.load(f)
            # If it's in old format (single user), convert to multi-user format
            if "username" in data and not isinstance(data.get("username"), dict):
                return {data["username"]: data}
            return data
        except json.JSONDecodeError:
            return {}


def save_data(users_dict):
    """Save all users to the JSON file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(JSON_PATH) if os.path.dirname(JSON_PATH) else ".", exist_ok=True)
    
    with open(JSON_PATH, "w") as f:
        json.dump(users_dict, f, indent=2)


def load_user(username=None):
    """
    Load a specific user by username.
    If no username is provided, return the first user.
    """
    data = load_data()
    
    if username:
        return data.get(username)
    
    # Fallback: return first user
    if data:
        return list(data.values())[0]
    return None


def save_user(username_or_data, user_data=None):
    """
    Save a single user to the JSON file.
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