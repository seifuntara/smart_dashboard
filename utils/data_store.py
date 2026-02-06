import json

DATA_PATH = "data/users.json"

def load_user():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_user(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)
