import os
import requests
import google.generativeai as genai
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Lấy biến môi trường từ Render
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Hàm gọi Gemini được viết gọn lại để tránh lỗi khởi tạo
def ask_gemini(message):
    try:
        if not GEMINI_API_KEY:
            return "Thiếu API Key của Gemini."
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Chỉ dẫn cho bot
        response = model.generate_content(f"Bạn là trợ lý bán hàng. Hãy trả lời câu hỏi: {message}")
        
        if response and response.text:
            return response.text
        return "Bot đang suy nghĩ..."
    except Exception as e:
        print(f"Lỗi kết nối Gemini: {e}")
        return "Xin lỗi, mình đang gặp chút trục trặc hệ thống."

@app.route("/", methods=["GET"])
def home():
    return "Bot is active!", 200

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
                    
                    # Gọi hàm xử lý Gemini
                    ai_reply = ask_gemini(user_text)
                    
                    # Gửi lại tin nhắn
                    send_fb_message(sender_id, ai_reply)
    return "OK", 200

def send_fb_message(sender_id, text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    try:
        requests.post(url, json={"recipient": {"id": sender_id}, "message": {"text": text}})
    except Exception as e:
        print(f"Lỗi gửi tin: {e}")

if __name__ == "__main__":
    # Render yêu cầu dùng PORT từ môi trường
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
