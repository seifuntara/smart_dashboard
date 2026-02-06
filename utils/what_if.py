from utils.finance import get_transactions_df
from utils.data_store import load_user

def simulate_category_change(category, delta):
    """
    delta: negative means reduce spend
    """
    df = get_transactions_df()
    user = load_user()

    current = df[df["category"] == category]["amount"].sum()
    simulated = max(current + delta, 0)

    monthly_spend = df["amount"].sum()
    new_total = monthly_spend - current + simulated

    savings = user["profile"]["monthly_income"] - new_total

    return {
        "current_category_spend": current,
        "new_category_spend": simulated,
        "new_total_spend": new_total,
        "new_savings": savings
    }
