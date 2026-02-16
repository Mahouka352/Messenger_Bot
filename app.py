import os
import requests
import traceback
import google.generativeai as genai
from flask import Flask, request
from dotenv import load_dotenv

# Load .env (local only, Render sẽ dùng Environment Variables)
load_dotenv()

app = Flask(__name__)

# ===== ENV VARIABLES =====
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY is missing!")

# ===== CONFIGURE GEMINI =====
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ===== HOME ROUTE =====
@app.route("/", methods=["GET"])
def home():
    return "Messenger Bot is running!", 200

# ===== VERIFY WEBHOOK =====
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verification failed", 403

# ===== RECEIVE MESSAGE =====
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("📩 Incoming data:", data)

        if data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging in entry.get("messaging", []):

                    sender_id = messaging["sender"]["id"]

                    if "message" in messaging and "text" in messaging["message"]:
                        user_message = messaging["message"]["text"]
                        print("👤 User:", user_message)

                        ai_reply = ask_gemini(user_message)

                        send_message(sender_id, ai_reply)

        return "OK", 200

    except Exception:
        print("🔥 WEBHOOK ERROR:")
        traceback.print_exc()
        return "Error", 500

# ===== GEMINI FUNCTION =====
def ask_gemini(message):
    try:
        prompt = f"Bạn là trợ lý bán hàng chuyên nghiệp. Trả lời ngắn gọn, dễ hiểu: {message}"

        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            reply = response.text.strip()
            print("🤖 Gemini:", reply)
            return reply
        else:
            print("⚠️ Empty response from Gemini")
            return "Xin lỗi, hệ thống đang bận."

    except Exception:
        print("🔥 GEMINI ERROR:")
        traceback.print_exc()
        return "Xin lỗi, hệ thống đang bận."

# ===== SEND MESSAGE TO FACEBOOK =====
def send_message(sender_id, message):
    try:
        url = "https://graph.facebook.com/v18.0/me/messages"
        params = {"access_token": PAGE_ACCESS_TOKEN}

        payload = {
            "recipient": {"id": sender_id},
            "message": {"text": message}
        }

        response = requests.post(url, params=params, json=payload)

        print("📤 Facebook response:", response.text)

    except Exception:
        print("🔥 SEND ERROR:")
        traceback.print_exc()

# ===== RUN APP =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
