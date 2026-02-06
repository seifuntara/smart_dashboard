from utils.finance import spending_by_category, monthly_spending
from utils.data_store import load_user

def get_analytics_context():
    user = load_user()

    return {
        "spending_by_category": spending_by_category(),
        "monthly_spending": monthly_spending(),
        "recent_transactions": user.get("transactions", [])[-5:]
    }
