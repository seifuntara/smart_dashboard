from utils.data_store import load_user

def authenticate(username, password):
    user = load_user()
    return (
        user["username"] == username and
        user["password"] == password
    )
