import os
import time
import requests
from flask import Flask, request

app = Flask(__name__)

# =========================
# ENVIRONMENT VARIABLES
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Gemini model
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

# Telegram API
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Gemini API
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/"
    f"v1beta/models/{GEMINI_MODEL}:generateContent"
)


# =========================
# SEND TELEGRAM MESSAGE
# =========================

def send_message(chat_id, text):
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram Error:", e)


# =========================
# ASK GEMINI AI
# =========================

def ask_gemini(text):

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are ItzNav Bot, a friendly and helpful "
                            "personal AI assistant. Give clear, useful and "
                            "easy-to-understand answers.\n\n"
                            f"User: {text}"
                        )
                    }
                ]
            }
        ]
    }

    response = requests.post(
        GEMINI_URL,
        headers=headers,
        params={
            "key": GEMINI_API_KEY
        },
        json=data,
        timeout=30
    )

    # Raise error if Gemini returns 4xx/5xx
    response.raise_for_status()

    result = response.json()

    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]

    except (KeyError, IndexError, TypeError):
        print("Unexpected Gemini response:", result)
        raise Exception("Invalid response received from Gemini")


# =========================
# HOME
# =========================

@app.route("/", methods=["GET"])
def home():
    return "ItzNav Bot is running! 🤖"


# =========================
# TELEGRAM WEBHOOK
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    if not data:
        return "OK"

    message = data.get("message")

    if not message:
        return "OK"

    chat = message.get("chat")

    if not chat:
        return "OK"

    chat_id = chat.get("id")

    text = message.get("text", "").strip()

    if not text:
        return "OK"


    # =========================
    # /START COMMAND
    # =========================

    if text == "/start":

        send_message(
            chat_id,
            "👋 Hello!\n\n"
            "I'm ItzNav Bot 🤖\n"
            "Your personal AI assistant.\n\n"
            "Ask me anything! 🚀\n\n"
            "Type /help to see commands."
        )

        return "OK"


    # =========================
    # /HELP COMMAND
    # =========================

    if text == "/help":

        send_message(
            chat_id,
            "🤖 ItzNav Bot Commands\n\n"
            "/start - Start the bot\n"
            "/help - Show help\n\n"
            "💬 Send me any message and I'll answer using AI!"
        )

        return "OK"


    # =========================
    # AI RESPONSE WITH RETRY
    # =========================

    max_retries = 3

    for attempt in range(max_retries):

        try:

            print(
                f"Gemini request attempt "
                f"{attempt + 1}/{max_retries}"
            )

            reply = ask_gemini(text)

            send_message(chat_id, reply)

            print("Gemini response sent successfully.")

            break


        except Exception as e:

            print(
                f"Gemini Error "
                f"(attempt {attempt + 1}/{max_retries}):",
                e
            )

            # Retry after increasing delay
            if attempt < max_retries - 1:

                wait_time = 2 ** attempt

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                send_message(
                    chat_id,
                    "⚠️ Gemini is temporarily busy.\n\n"
                    "Please try again in a moment."
                )


    return "OK"


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )