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

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Models are tried in this order
GEMINI_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash"
]


# =========================
# TELEGRAM MESSAGE
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
# GEMINI AI
# =========================

def ask_gemini(text):

    last_error = None

    for model in GEMINI_MODELS:

        print(f"Trying Gemini model: {model}")

        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{model}:generateContent"
        )

        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "You are ItzNav Bot, a friendly personal "
                                "AI assistant created by Navneet.\n\n"
                                "Answer clearly, naturally and helpfully. "
                                "Keep answers understandable and useful.\n\n"
                                f"User message:\n{text}"
                            )
                        }
                    ]
                }
            ]
        }

        try:

            response = requests.post(
                url,
                params={
                    "key": GEMINI_API_KEY
                },
                headers={
                    "Content-Type": "application/json"
                },
                json=data,
                timeout=30
            )

            print(
                f"Gemini {model} status:",
                response.status_code
            )

            # Successful response
            if response.status_code == 200:

                result = response.json()

                reply = (
                    result["candidates"][0]
                    ["content"]["parts"][0]["text"]
                )

                return reply

            # Model temporarily busy
            if response.status_code in [429, 500, 503]:

                print(
                    f"{model} temporarily unavailable."
                )

                last_error = response.text

                # Try next model
                time.sleep(1)

                continue

            # Other error
            print(
                f"Gemini API error from {model}:",
                response.text
            )

            last_error = response.text

        except Exception as e:

            print(
                f"Connection error with {model}:",
                e
            )

            last_error = str(e)

    raise Exception(
        f"All Gemini models failed: {last_error}"
    )


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
    # START
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
    # HELP
    # =========================

    if text == "/help":

        send_message(
            chat_id,
            "🤖 ItzNav Bot Commands\n\n"
            "/start - Start the bot\n"
            "/help - Show help\n\n"
            "💬 Send me any message and "
            "I'll answer using AI!"
        )

        return "OK"


    # =========================
    # AI RESPONSE
    # =========================

    try:

        reply = ask_gemini(text)

        send_message(
            chat_id,
            reply
        )

        print("AI response sent successfully.")

    except Exception as e:

        print("Final Gemini Error:", e)

        send_message(
            chat_id,
            "⚠️ I'm having trouble connecting "
            "to my AI right now.\n\n"
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