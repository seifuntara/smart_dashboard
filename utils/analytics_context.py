from utils.finance import spending_by_category, monthly_spending
from utils.data_store import load_user

def get_analytics_context(username):
    user = load_user(username)
    if not user: return {}

    return {
        "spending_by_category": spending_by_category(username),
        "monthly_spending": monthly_spending(username),
        "recent_transactions": user.get("transactions", [])[-5:]
    }