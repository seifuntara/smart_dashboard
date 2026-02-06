from utils.llm_test import ask_groq
from utils.analytics_context import get_analytics_context


def format_analytics_context(context: dict) -> str:
    """
    Converts analytics data into a readable summary for the LLM.
    """
    lines = []

    # Spending by category
    lines.append("Spending by category:")
    for cat, amt in context["spending_by_category"].items():
        lines.append(f"- {cat}: ${amt:.2f}")

    # Monthly spending
    lines.append("\nMonthly spending totals:")
    for month, total in context["monthly_spending"].items():
        lines.append(f"- {month}: ${total:.2f}")

    # Recent transactions
    lines.append("\nRecent transactions:")
    for txn in context["recent_transactions"]:
        lines.append(
            f"- {txn['date']}: ${txn['amount']} on {txn['category']} ({txn.get('merchant','')})"
        )

    return "\n".join(lines)


def handle_message(user_input, username=None, screen_context=None):
    # Check for human handoff keywords
    handoff_keywords = ["human", "agent", "representative"]
    
    if any(keyword in user_input.lower() for keyword in handoff_keywords):
        return (
            "I see you need human assistance. \n\n"
            "I have forwarded your request to our support team. "
            "An agent will contact you at your registered email within 24 hours. "
            "Ticket ID: #99281"
        )

    view = (screen_context or {}).get("view", "assistant")

    # ---------------- ANALYTICS MODE ----------------
    if "analytics" in view and username:
        analytics_context = get_analytics_context(username)
        analytics_summary = format_analytics_context(analytics_context)

        prompt = f"""
You are a financial analytics assistant.

The user is looking at a dashboard with charts and tables.

Here is the current analytics data:
{analytics_summary}

Rules:
- Do NOT invent numbers
- Only use the data above
- Explain patterns and insights clearly
- Give practical suggestions if relevant

User question:
{user_input}
"""
        return ask_groq(prompt)

    # ---------------- DEFAULT MODE ----------------
    prompt = f"""
You are a helpful banking assistant.

User question:
{user_input}
"""
    return ask_groq(prompt)