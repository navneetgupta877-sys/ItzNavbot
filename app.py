import os
import time
import requests
from flask import Flask, request

app = Flask(__name__)

# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not BOT_TOKEN:
    print("WARNING: BOT_TOKEN is missing!")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is missing!")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# =========================================================
# GEMINI MODELS
# =========================================================
# Primary model first.
# If temporarily unavailable, fallback models are tried.

GEMINI_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash"
]

# =========================================================
# SEND TELEGRAM MESSAGE
# =========================================================

def send_message(chat_id, text):

    if not text:
        text = "Sorry, I couldn't generate a response."

    # Telegram messages have a maximum length.
    # Split long AI responses safely.
    max_length = 4000

    for i in range(0, len(text), max_length):

        part = text[i:i + max_length]

        try:

            response = requests.post(
                f"{TELEGRAM_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": part
                },
                timeout=15
            )

            print(
                "Telegram status:",
                response.status_code
            )

        except Exception as e:

            print(
                "Telegram Error:",
                e
            )

# =========================================================
# ASK GEMINI
# =========================================================

def ask_gemini(user_text):

    if not GEMINI_API_KEY:
        raise Exception(
            "GEMINI_API_KEY environment variable is missing."
        )

    last_error = "Unknown Gemini error"

    for model in GEMINI_MODELS:

        print(
            f"Trying Gemini model: {model}"
        )

        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{model}:generateContent"
        )

        payload = {

            "system_instruction": {

                "parts": [

                    {
                        "text": (
                            "You are ItzNav Bot, a personal AI "
                            "assistant created by Navneet.\n\n"

                            "Your personality:\n"
                            "- Friendly and helpful\n"
                            "- Smart and practical\n"
                            "- Explain things clearly\n"
                            "- Use simple language when possible\n"
                            "- You can understand Hindi, Hinglish "
                            "and English.\n"
                            "- Reply in the same language style "
                            "the user uses.\n"
                            "- Do not unnecessarily repeat the "
                            "user's question.\n"
                            "- Give useful and direct answers.\n"
                            "- If you don't know something, "
                            "say so honestly.\n\n"

                            "User message:"
                        )
                    }

                ]
            },

            "contents": [

                {
                    "role": "user",

                    "parts": [
                        {
                            "text": user_text
                        }
                    ]
                }

            ],

            "generationConfig": {

                "temperature": 0.7,

                "maxOutputTokens": 2048

            }

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

                json=payload,

                timeout=45

            )

            print(
                f"Gemini {model} HTTP:",
                response.status_code
            )

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            if response.status_code == 200:

                result = response.json()

                candidates = result.get(
                    "candidates",
                    []
                )

                if not candidates:

                    raise Exception(
                        "Gemini returned no candidates."
                    )

                content = candidates[0].get(
                    "content",
                    {}
                )

                parts = content.get(
                    "parts",
                    []
                )

                if not parts:

                    raise Exception(
                        "Gemini returned empty content."
                    )

                reply = parts[0].get(
                    "text",
                    ""
                )

                if not reply:

                    raise Exception(
                        "Gemini returned empty text."
                    )

                print(
                    f"Gemini success using {model}"
                )

                return reply.strip()

            # -------------------------------------------------
            # TEMPORARY SERVER / RATE LIMIT ERROR
            # -------------------------------------------------

            if response.status_code in [429, 500, 502, 503, 504]:

                last_error = response.text

                print(
                    f"{model} temporarily unavailable."
                )

                # Small retry delay
                time.sleep(2)

                continue

            # -------------------------------------------------
            # AUTHENTICATION ERROR
            # -------------------------------------------------

            if response.status_code in [400, 401, 403]:

                last_error = response.text

                print(
                    "Gemini API authentication/request error:"
                )

                print(response.text)

                # Don't keep retrying the same bad API key.
                raise Exception(
                    f"Gemini API error {response.status_code}: "
                    f"{response.text}"
                )

            # -------------------------------------------------
            # OTHER ERROR
            # -------------------------------------------------

            last_error = response.text

            print(
                f"Gemini error from {model}:"
            )

            print(response.text)

        except requests.exceptions.Timeout:

            last_error = (
                f"{model} request timed out."
            )

            print(last_error)

            continue

        except requests.exceptions.RequestException as e:

            last_error = str(e)

            print(
                "Network error:",
                e
            )

            continue

        except Exception as e:

            last_error = str(e)

            print(
                "Gemini processing error:",
                e
            )

            # Authentication / invalid request errors
            # should not continue blindly.
            raise

    raise Exception(
        f"All Gemini models failed. "
        f"Last error: {last_error}"
    )

# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return "ItzNav Bot is running! 🤖"

# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health", methods=["GET"])
def health():

    return "OK"

# =========================================================
# TELEGRAM WEBHOOK
# =========================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:
            return "OK"

        message = data.get(
            "message"
        )

        if not message:
            return "OK"

        chat = message.get(
            "chat"
        )

        if not chat:
            return "OK"

        chat_id = chat.get(
            "id"
        )

        text = message.get(
            "text",
            ""
        ).strip()

        if not chat_id:
            return "OK"

        if not text:
            return "OK"

        print(
            f"Telegram message: {text}"
        )

        # =====================================================
        # START COMMAND
        # =====================================================

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

        # =====================================================
        # HELP COMMAND
        # =====================================================

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

        # =====================================================
        # AI RESPONSE
        # =====================================================

        try:

            reply = ask_gemini(
                text
            )

            send_message(
                chat_id,
                reply
            )

            print(
                "AI response sent successfully."
            )

        except Exception as e:

            print(
                "Final AI Error:",
                e
            )

            send_message(

                chat_id,

                "⚠️ I'm having trouble connecting "
                "to my AI right now.\n\n"
                "Please try again in a moment."

            )

        return "OK"

    except Exception as e:

        print(
            "Webhook Error:",
            e
        )

        return "OK"

# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    print(
        f"ItzNav Bot starting on port {port}"
    )

    app.run(
        host="0.0.0.0",
        port=port
    )