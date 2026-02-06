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


def handle_message(user_input, screen_context=None):
    # Honor explicit role selected in the UI (if provided)
    role = (screen_context or {}).get("role", "agent")

    # If user selected a human, return a handoff message immediately
    if role == "human":
        return (
            "I see you requested human assistance.\n\n"
            "I have forwarded your request to our support team. "
            "An agent will contact you at your registered email within 24 hours. "
            "Ticket ID: #99281"
        )

    view = (screen_context or {}).get("view", "assistant")

    # ---------------- ANALYTICS MODE ----------------
    if "analytics" in view:
        analytics_context = get_analytics_context()
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

    # ---------------- REPRESENTATIVE MODE ----------------
    if role == "representative":
        prompt = f"""
You are a human customer support representative for a bank. Respond empathetically and clearly, using a helpful and professional tone. If action is required, explain next steps (e.g., refunds, escalation, or how to contact support). Keep answers concise and include any safety or verification steps where appropriate.

User question:
{user_input}
"""
        return ask_groq(prompt)

    # ---------------- DEFAULT/AGENT MODE ----------------
    prompt = f"""
You are a helpful banking assistant.

User question:
{user_input}
"""
    return ask_groq(prompt)