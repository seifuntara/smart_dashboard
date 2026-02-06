from utils.finance import get_transactions_df
from utils.data_store import load_user

def simulate_category_change(username, category, delta):
    df = get_transactions_df(username)
    user = load_user(username)

    if not user or df.empty: return {"error": "No data"}

    current = df[df["category"] == category]["amount"].sum() if category in df["category"].values else 0
    simulated = max(current + delta, 0)
    
    # Simple calculation based on new total
    monthly_spend = df["amount"].sum()
    new_total = monthly_spend - current + simulated
    
    return {
        "current_category_spend": current,
        "new_category_spend": simulated,
        "new_total_spend": new_total,
        "new_savings": user["profile"]["monthly_income"] - new_total
    }