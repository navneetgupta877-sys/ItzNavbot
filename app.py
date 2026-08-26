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
    print("WARNING: BOT_TOKEN is not set!")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set!")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


# =========================================================
# GEMINI MODELS
# =========================================================

GEMINI_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash"
]


# =========================================================
# TELEGRAM SEND MESSAGE
# =========================================================

def send_message(chat_id, text):

    try:

        if not text:
            text = "⚠️ I couldn't generate a response."

        # Telegram has a message length limit.
        # Split very long AI responses.
        max_length = 4000

        for i in range(0, len(text), max_length):

            part = text[i:i + max_length]

            response = requests.post(
                f"{BASE_URL}/sendMessage",
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

            if response.status_code != 200:
                print(
                    "Telegram error:",
                    response.text
                )

    except Exception as e:

        print(
            "Telegram Error:",
            e
        )


# =========================================================
# GEMINI AI
# =========================================================

def ask_gemini(user_text):

    if not GEMINI_API_KEY:

        raise Exception(
            "GEMINI_API_KEY environment variable is missing."
        )


    # -----------------------------------------------------
    # Personality / System Instructions
    # -----------------------------------------------------

    prompt = f"""
You are ItzNav Bot 🤖, a friendly and intelligent personal AI
assistant created by Navneet.

Your job is to help the user with questions, learning,
technology, coding, daily life, engineering, explanations,
ideas and general conversation.

Rules:

1. Be helpful, friendly and natural.
2. Understand the user's intent before answering.
3. Give clear and practical answers.
4. If the user asks a technical question, explain step-by-step.
5. Don't unnecessarily make answers very long.
6. Use simple language when possible.
7. You can use emojis naturally, but don't overuse them.
8. If you don't know something, honestly say so.
9. Never claim that you performed an action that you did not perform.
10. Answer the user's actual question instead of giving generic replies.

User message:

{user_text}
"""


    last_error = None


    # =====================================================
    # TRY EACH MODEL
    # =====================================================

    for model in GEMINI_MODELS:

        print(
            f"Trying Gemini model: {model}"
        )


        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{model}:generateContent"
        )


        data = {

            "contents": [

                {
                    "parts": [

                        {
                            "text": prompt
                        }

                    ]
                }

            ],

            "generationConfig": {

                "temperature": 0.7,

                "maxOutputTokens": 2048

            }

        }


        # =================================================
        # RETRIES
        # =================================================

        for attempt in range(3):

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

                    timeout=40

                )


                print(
                    f"Gemini {model} "
                    f"attempt {attempt + 1} "
                    f"status: {response.status_code}"
                )


                # -----------------------------------------
                # SUCCESS
                # -----------------------------------------

                if response.status_code == 200:

                    result = response.json()


                    try:

                        reply = (
                            result["candidates"][0]
                            ["content"]["parts"][0]["text"]
                        )

                    except (KeyError, IndexError, TypeError):

                        print(
                            "Unexpected Gemini response:",
                            result
                        )

                        raise Exception(
                            "Gemini returned an unexpected response."
                        )


                    if reply and reply.strip():

                        return reply.strip()


                    raise Exception(
                        "Gemini returned an empty response."
                    )


                # -----------------------------------------
                # TEMPORARY ERRORS
                # -----------------------------------------

                if response.status_code in [429, 500, 502, 503, 504]:

                    last_error = response.text

                    print(
                        f"Gemini {model} temporarily "
                        f"unavailable."
                    )

                    # Exponential backoff:
                    # 2 sec → 4 sec → 8 sec

                    wait_time = 2 ** attempt

                    print(
                        f"Waiting {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                    continue


                # -----------------------------------------
                # API KEY / BAD REQUEST / OTHER ERROR
                # -----------------------------------------

                print(
                    f"Gemini API error from {model}:"
                )

                print(
                    response.text
                )

                last_error = response.text

                # Don't keep retrying permanent errors.
                break


            except requests.exceptions.Timeout as e:

                print(
                    f"Gemini timeout "
                    f"({model}, attempt {attempt + 1}):",
                    e
                )

                last_error = str(e)

                time.sleep(2 ** attempt)


            except requests.exceptions.RequestException as e:

                print(
                    f"Gemini connection error "
                    f"({model}):",
                    e
                )

                last_error = str(e)

                time.sleep(2 ** attempt)


            except Exception as e:

                print(
                    f"Gemini unexpected error "
                    f"({model}):",
                    e
                )

                last_error = str(e)

                break


        print(
            f"Model {model} failed."
        )


    # =====================================================
    # ALL MODELS FAILED
    # =====================================================

    raise Exception(
        f"All Gemini models failed: {last_error}"
    )


# =========================================================
# HOME PAGE
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


        message = data.get("message")


        if not message:

            return "OK"


        chat = message.get("chat")


        if not chat:

            return "OK"


        chat_id = chat.get("id")


        if not chat_id:

            return "OK"


        text = message.get(
            "text",
            ""
        ).strip()


        if not text:

            return "OK"


        print(
            f"Message received: {text}"
        )


        # =================================================
        # START COMMAND
        # =================================================

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


        # =================================================
        # HELP COMMAND
        # =================================================

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


        # =================================================
        # AI RESPONSE
        # =================================================

        try:

            print(
                "Sending message to Gemini..."
            )


            reply = ask_gemini(text)


            print(
                "Gemini response received."
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
                "Final Gemini Error:",
                e
            )


            send_message(

                chat_id,

                "⚠️ My AI service is temporarily "
                "unavailable.\n\n"
                "Please try again in a few seconds. 🤖"

            )


        return "OK"


    except Exception as e:

        print(
            "Webhook Error:",
            e
        )

        # Always return 200 so Telegram
        # doesn't repeatedly resend the update.

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
        f"ItzNav Bot starting on port {port}..."
    )


    app.run(

        host="0.0.0.0",

        port=port

    )