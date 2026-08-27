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

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# =========================================================
# GEMINI MODELS
# =========================================================

# Fastest/primary model first.
# If temporarily unavailable, fallback will be used.

GEMINI_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash"
]

# Reuse HTTP connections = slightly faster requests
session = requests.Session()

# =========================================================
# TELEGRAM MESSAGE
# =========================================================

def send_message(chat_id, text):

    if not text:
        text = "Sorry, I couldn't generate a response."

    # Telegram message limit
    max_length = 4000

    for i in range(0, len(text), max_length):

        part = text[i:i + max_length]

        try:

            response = session.post(
                f"{TELEGRAM_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": part
                },
                timeout=10
            )

            print(
                "Telegram:",
                response.status_code
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
            "GEMINI_API_KEY is missing."
        )

    last_error = "Unknown error"

    for model in GEMINI_MODELS:

        print(
            f"Trying model: {model}"
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
                            "You are ItzNav Bot, a friendly "
                            "personal AI assistant created by Navneet.\n"
                            "Answer clearly, naturally and helpfully.\n"
                            "Understand Hindi, Hinglish and English.\n"
                            "Reply in the same language as the user.\n"
                            "Be concise unless the user asks for detail."
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

                # Lower = faster response
                "maxOutputTokens": 1024

            }

        }

        try:

            response = session.post(

                url,

                params={
                    "key": GEMINI_API_KEY
                },

                headers={
                    "Content-Type": "application/json"
                },

                json=payload,

                timeout=30

            )

            print(
                f"{model}: HTTP {response.status_code}"
            )

            # =================================================
            # SUCCESS
            # =================================================

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

                parts = (
                    candidates[0]
                    .get("content", {})
                    .get("parts", [])
                )

                if not parts:

                    raise Exception(
                        "Gemini returned empty response."
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
                    f"SUCCESS: {model}"
                )

                return reply.strip()

            # =================================================
            # TEMPORARY ERROR
            # =================================================

            if response.status_code in [
                429,
                