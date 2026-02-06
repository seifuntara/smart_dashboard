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
    # Cast all values to native Python types so jsonify works
    income = float(user.get("profile", {}).get("monthly_income", 0))
    savings_goal = float(user.get("profile", {}).get("savings_goal", 0))
    monthly_spend_f = float(monthly_spend)
    current_f = float(current)
    simulated_f = float(simulated)
    new_total_f = float(new_total)
    original_savings = income - monthly_spend_f
    new_savings = income - new_total_f
    original_deviation = original_savings - savings_goal
    new_deviation = new_savings - savings_goal
    meets_goal = bool(new_savings >= savings_goal)

    return {
        "current_category_spend": current_f,
        "new_category_spend": simulated_f,
        "new_total_spend": new_total_f,
        "new_savings": new_savings,
        "savings_goal": savings_goal,
        "original_savings": original_savings,
        "original_deviation": original_deviation,
        "new_deviation": new_deviation,
        "meets_goal": meets_goal
    }


def simulate_multi_category_change(username, changes):
    """Simulate multiple category changes.

    `changes` should be a dict mapping category -> delta (float).
    Delta can be negative (spend less) or positive (spend more).
    Returns aggregated results including per-category breakdown.
    """
    df = get_transactions_df(username)
    user = load_user(username)

    if not user or df.empty:
        return {"error": "No data"}

    monthly_spend = df["amount"].sum()
    new_total = monthly_spend
    breakdown = {}

    for category, delta in changes.items():
        try:
            delta = float(delta)
        except Exception:
            delta = 0.0

        current = df[df["category"] == category]["amount"].sum() if category in df["category"].values else 0.0
        simulated = max(current + delta, 0.0)

        breakdown[category] = {
            "current": float(current),
            "simulated": float(simulated),
            "delta": float(delta)
        }

        new_total = new_total - current + simulated

    income = float(user.get("profile", {}).get("monthly_income", 0))
    savings_goal = float(user.get("profile", {}).get("savings_goal", 0))
    original_total_spend_f = float(monthly_spend)
    new_total_f = float(new_total)
    original_savings = income - original_total_spend_f
    new_savings = income - new_total_f
    original_deviation = original_savings - savings_goal
    new_deviation = new_savings - savings_goal
    meets_goal = bool(new_savings >= savings_goal)

    return {
        "breakdown": breakdown,
        "original_total_spend": original_total_spend_f,
        "new_total_spend": new_total_f,
        "original_savings": original_savings,
        "new_savings": new_savings,
        "savings_goal": savings_goal,
        "original_deviation": original_deviation,
        "new_deviation": new_deviation,
        "meets_goal": meets_goal
    }