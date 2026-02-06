import pandas as pd
from utils.data_store import load_user

def get_transactions_df(username):
    user = load_user(username)
    if not user or "transactions" not in user:
        return pd.DataFrame(columns=["date", "amount", "category", "merchant"])
    
    df = pd.DataFrame(user["transactions"])
    df["date"] = pd.to_datetime(df["date"])
    return df

def spending_by_category(username):
    df = get_transactions_df(username)
    if df.empty: return {}
    return df.groupby("category")["amount"].sum().to_dict()

def monthly_spending(username):
    df = get_transactions_df(username)
    if df.empty: return {}
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df.groupby("month")["amount"].sum().to_dict()