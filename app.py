from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from utils.auth import authenticate, register_user
from utils.chatbot import handle_message
from utils.finance import spending_by_category, monthly_spending
from utils.what_if import simulate_category_change, simulate_multi_category_change
from utils.data_store import load_user
from utils.data_store import save_user
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "dummy_bank_secret_hai"


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if register_user(username, password):
            session["username"] = username
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="User already exists", mode="register")

    return render_template("login.html", mode="register")


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if authenticate(username, password):
            session["username"] = username
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/chat", methods=["POST"])
def chat():
    if "username" not in session:
        return jsonify({"reply": "Session expired. Please login again."}), 401
    
    data = request.json
    user_message = data["message"]
    screen_context = data.get("context", {})

    reply = handle_message(
        user_input=user_message,
        username=session["username"],
        screen_context=screen_context
    )

    return jsonify({"reply": reply})


@app.route("/analytics/transactions")
def transactions_data():
    if "username" not in session:
        return jsonify([])
    user = load_user(session["username"])
    return jsonify(user.get("transactions", []) if user else [])


@app.route("/analytics/category")
def category_analytics():
    if "username" not in session:
        return jsonify({})
    return jsonify(spending_by_category(session["username"]))


@app.route("/analytics/monthly")
def monthly_analytics():
    if "username" not in session:
        return jsonify({})
    return jsonify(monthly_spending(session["username"]))


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    user = load_user(session["username"])
    profile = user.get("profile", {}) if user else {}

    return render_template(
        "dashboard.html",
        username=session["username"],
        profile=profile
    )


# @app.route("/chat", methods=["POST"])
# def chat():
#     if "username" not in session:
#         return jsonify({"reply": "Session expired. Please login again."})
#
#     user_message = request.json["message"]
#
#     bot_reply = handle_message(
#         username=session["username"],
#         user_input=user_message
#     )
#
#     return jsonify({"reply": bot_reply})


@app.route("/analytics-data")
def analytics_data():
    if "username" not in session:
        return jsonify({})
    return jsonify(spending_by_category(session["username"]))


@app.route("/add-transaction", methods=["POST"])
def add_transaction():
    if "username" not in session:
        return jsonify({"status": "error"}), 401

    from utils.data_store import load_user, save_user

    try:
        transaction = {
            "date": request.form["date"],
            "amount": float(request.form["amount"]),
            "category": request.form["category"],
            "merchant": request.form.get("merchant", "")
        }

        user = load_user(session["username"])
        if not user:
            return jsonify({"status": "error"}), 404

        user.setdefault("transactions", []).append(transaction)
        save_user(session["username"], user)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("Add transaction error:", e)
        return jsonify({"status": "error"}), 500
# =====================================================


@app.route("/what-if", methods=["POST"])
def what_if():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    # Support either single change (category+delta) or multiple changes via `changes` dict
    if data.get("changes"):
        result = simulate_multi_category_change(
            username=session["username"],
            changes=data["changes"]
        )
    else:
        result = simulate_category_change(
            username=session["username"],
            category=data.get("category", ""),
            delta=float(data.get("delta", 0))
        )
    return jsonify(result)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/update-profile", methods=["POST"])
def update_profile():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.json or {}
    try:
        user = load_user(session["username"])
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        profile = user.setdefault("profile", {})
        # Only update numeric fields if provided
        if "monthly_income" in data:
            profile["monthly_income"] = float(data["monthly_income"]) if data["monthly_income"] != "" else profile.get("monthly_income", 0)
        if "monthly_budget" in data:
            profile["monthly_budget"] = float(data["monthly_budget"]) if data["monthly_budget"] != "" else profile.get("monthly_budget", 0)
        if "savings_goal" in data:
            profile["savings_goal"] = float(data["savings_goal"]) if data["savings_goal"] != "" else profile.get("savings_goal", 0)

        save_user(session["username"], user)
        return jsonify({"status": "success", "profile": profile})

    except Exception as e:
        print("Update profile error:", e)
        return jsonify({"status": "error", "message": "Server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
