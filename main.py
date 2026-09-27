import os
import sqlite3
from flask import Flask, request
import requests

TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

DB = "users.db"


def db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0
        )
    """)
    return conn


def send_message(chat_id, text):
    requests.post(
        f"{API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=20
    )


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


@app.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json()

    if "message" not in update:
        return "OK"

    message = update["message"]
    user = message["from"]

    user_id = user["id"]
    username = user.get("username", "")
    text = message.get("text", "")

    conn = db()

    existing = conn.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    if not existing:
        conn.execute(
            "INSERT INTO users(user_id, username) VALUES (?,?)",
            (user_id, username)
        )
        conn.commit()

    if text == "/start":

        row = conn.execute(
            "SELECT points, referrals FROM users WHERE user_id=?",
            (user_id,)
        ).fetchone()

        points, referrals = row

        send_message(
            user_id,
            f"""🎉 Welcome!

💰 Your Points: {points}
👥 Referrals: {referrals}

Commands:

💰 /balance
🎁 /daily
👥 /referral
📤 /withdraw
"""
        )

    elif text == "/balance":

        points = conn.execute(
            "SELECT points FROM users WHERE user_id=?",
            (user_id,)
        ).fetchone()[0]

        send_message(
            user_id,
            f"💰 Your balance: {points} points"
        )

    elif text == "/daily":

        conn.execute(
            "UPDATE users SET points=points+10 WHERE user_id=?",
            (user_id,)
        )
        conn.commit()

        send_message(
            user_id,
            "🎁 Daily bonus received!\n\n+10 points"
        )

    elif text == "/referral":

        bot_username = requests.get(
            f"{API}/getMe",
            timeout=20
        ).json()["result"]["username"]

        link = f"https://t.me/{bot_username}?start={user_id}"

        send_message(
            user_id,
            f"""👥 Your referral link:

{link}

Invite friends and earn rewards!"""
        )

    elif text == "/withdraw":

        points = conn.execute(
            "SELECT points FROM users WHERE user_id=?",
            (user_id,)
        ).fetchone()[0]

        send_message(
            user_id,
            f"""📤 Withdrawal

Your balance: {points} points

Minimum withdrawal will be configured later."""
        )

    else:

        send_message(
            user_id,
            "Use /start to open the menu."
        )

    conn.close()

    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
