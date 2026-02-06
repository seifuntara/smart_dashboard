from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from utils.auth import authenticate
from utils.chatbot import handle_message
from utils.finance import spending_by_category, monthly_spending
from utils.what_if import simulate_category_change
from utils.data_store import load_user
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "dummy_bank_secret_hai"


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
    data = request.json
    user_message = data["message"]
    screen_context = data.get("context", {})

    reply = handle_message(
        user_input=user_message,
        screen_context=screen_context
    )

    return jsonify({"reply": reply})


@app.route("/analytics/transactions")
def transactions_data():
    user = load_user()
    return jsonify(user.get("transactions", []))


@app.route("/analytics/category")
def category_analytics():
    return jsonify(spending_by_category())


@app.route("/analytics/monthly")
def monthly_analytics():
    return jsonify(monthly_spending())


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session["username"]
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
    from utils.finance import spending_by_category
    return jsonify(spending_by_category())


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

        user = load_user()
        user.setdefault("transactions", []).append(transaction)
        save_user(user)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("Add transaction error:", e)
        return jsonify({"status": "error"}), 500
# =====================================================


@app.route("/what-if", methods=["POST"])
def what_if():
    data = request.json
    result = simulate_category_change(
        category=data["category"],
        delta=float(data["delta"])
    )
    return jsonify(result)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
