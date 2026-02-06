from utils.data_store import load_data, save_data

def authenticate(username, password):
    users = load_data()
    user = users.get(username)
    
    # Check if user exists and password matches
    if user and user["password"] == password:
        return True
    return False

def register_user(username, password):
    users = load_data()
    
    if username in users:
        return False  # User already exists
    
    # Create the new user structure
    users[username] = {
        "username": username,
        "password": password,
        "profile": {
            "monthly_income": 3000, 
            "monthly_budget": 2500,
            "savings_goal": 500
        },
        "accounts": {
            "checking_balance": 0.0,
            "savings_balance": 0.0
        },
        "transactions": [],
        "chat_history": []
    }
    
    save_data(users)
    return True