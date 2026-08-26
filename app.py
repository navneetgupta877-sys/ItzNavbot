import os
import requests
from flask import Flask, request
from google import genai
from google.genai import types

app = Flask(__name__)

# Telegram
TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# ItzNav Bot personality
SYSTEM_INSTRUCTION = """
You are ItzNav Bot 🤖, a friendly and intelligent personal AI assistant.

Your creator is Navneet.
Be helpful, friendly, respectful and practical.
You can speak in English, Hindi, or Hinglish depending on the user's language.

Keep normal answers concise and easy to understand.
For technical questions, explain step-by-step when useful.
If the user asks something you don't know, be honest instead of making up facts.

You are running inside a Telegram bot, so keep replies Telegram-friendly.
"""

# Simple short-term conversation memory
chat_history = {}


def send_message(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=10
    )


def ask_gemini(chat_id, user_text):
    # Get previous conversation
    history = chat_history.get(chat_id, [])

    # Add current message
    history.append({
        "role": "user",
        "parts": [{"text": user_text}]
    })

    # Keep only recent messages
    history = history[-10:]

    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            max_output_tokens=1000
        )
    )

    reply = response.text

    # Save conversation
    history.append({
        "role": "model",
        "parts": [{"text": reply}]
    })

    chat_history[chat_id] = history

    return reply


@app.route("/", methods=["GET"])
def home():
    return "ItzNav Bot is running! 🤖"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    if not data:
        return "OK"

    message = data.get("message")

    if not message:
        return "OK"

    chat = message.get("chat", {})
    chat_id = chat.get("id")

    text = message.get("text")

    if not chat_id or not text:
        return "OK"

    # /start command
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

    # /help command
    if text == "/help":
        send_message(
            chat_id,
            "🤖 ItzNav Bot Commands\n\n"
            "/start - Start the bot\n"
            "/help - Show help\n\n"
            "💬 Send me any message and I'll answer using AI!"
        )
        return "OK"

    # AI response
    try:
        reply = ask_gemini(chat_id, text)
        send_message(chat_id, reply)

    except Exception as e:
        print("Gemini Error:", e)
        send_message(
            chat_id,
            "⚠️ Sorry, I couldn't process that right now. Please try again."
        )

    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port) 