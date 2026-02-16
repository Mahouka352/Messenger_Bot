import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Cấu hình Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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
        if data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging in entry.get("messaging", []):
                    sender_id = messaging["sender"]["id"]

                    if "message" in messaging and "text" in messaging["message"]:
                        user_message = messaging["message"]["text"]

                        # Đổi từ ask_chatgpt sang ask_gemini
                        ai_reply = ask_gemini(user_message)
                        send_message(sender_id, ai_reply)

        return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "Error", 500

# ===== GEMINI FUNCTION (Thay thế hoàn toàn ChatGPT) =====
def ask_gemini(message):
    try:
        # Sử dụng model Gemini để tạo phản hồi
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [f"Bạn là trợ lý bán hàng chuyên nghiệp. Trả lời: {message}"]}
            ]
        )
        
        if response.text:
            return response.text
        else:
            return "Xin lỗi, hệ thống đang bận."

    except Exception as e:
        print("GEMINI ERROR:", e)
        return "Xin lỗi, hệ thống đang bận."

# ===== SEND MESSAGE TO USER =====
def send_message(sender_id, message):
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages"
        params = {"access_token": PAGE_ACCESS_TOKEN}

        payload = {
            "recipient": {"id": sender_id},
            "message": {"text": message}
        }

        r = requests.post(url, params=params, json=payload)
        print("SEND STATUS:", r.text)

    except Exception as e:
        print("SEND ERROR:", e)

# ===== RENDER PORT CONFIG (Giữ nguyên bản gốc của bạn) =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
