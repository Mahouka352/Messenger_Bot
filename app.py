import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

app = Flask(__name__)

# Cấu hình các Token từ Environment Variables trên Render
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Khởi tạo Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

def ask_gemini(message):
    try:
        # Bạn có thể chỉnh sửa tính cách bot ở phần content bên dưới
        response = model.generate_content(f"Bạn là trợ lý bán hàng chuyên nghiệp. Trả lời: {message}")
        return response.text if response.text else "Bot đang suy nghĩ..."
    except Exception as e:
        print(f"Lỗi Gemini: {e}")
        return "Hệ thống đang bận, bạn vui lòng nhắn lại sau."

@app.route("/", methods=["GET"])
def home():
    return "Bot Gemini is Live!", 200

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data and data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                if "message" in messaging and "text" in messaging["message"]:
                    user_text = messaging["message"]["text"]
                    # Gọi Gemini xử lý
                    ai_reply = ask_gemini(user_text)
                    # Gửi lại Messenger
                    send_fb_message(sender_id, ai_reply)
    return "OK", 200

def send_fb_message(sender_id, text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": sender_id}, "message": {"text": text}}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Lỗi gửi tin: {e}")

# QUAN TRỌNG: Không thay đổi phần này để Render nhận diện được Port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
