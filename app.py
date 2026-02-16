import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Cấu hình Token
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Cấu hình Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ===== HOME ROUTE =====
@app.route("/", methods=["GET"])
def home():
    return "Messenger Bot (Gemini AI) is running!", 200

# ===== VERIFY WEBHOOK =====
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK VERIFIED")
        return challenge, 200
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
                    
                    # Tránh trả lời tin nhắn của chính bot hoặc tin nhắn không có text
                    if "message" in messaging and "text" in messaging["message"]:
                        user_message = messaging["message"]["text"]
                        
                        # Gọi Gemini xử lý
                        ai_reply = ask_gemini(user_message)
                        
                        # Gửi lại cho Messenger
                        send_message(sender_id, ai_reply)

        return "OK", 200
    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "Error", 500

# ===== GEMINI FUNCTION =====
def ask_gemini(message):
    try:
        # Bạn có thể thêm chỉ dẫn cho Bot ở đây (System Instruction)
        prompt = f"Bạn là trợ lý bán hàng chuyên nghiệp. Hãy trả lời câu hỏi sau: {message}"
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text
        return "Bot đang suy nghĩ, bạn chờ chút nhé."
    except Exception as e:
        print("GEMINI ERROR:", e)
        return "Xin lỗi, mình gặp chút trục trặc khi kết nối AI."

# ===== SEND MESSAGE TO USER =====
def send_message(sender_id, message):
    try:
        url = "https://graph.facebook.com/v18.0/me/messages"
        params = {"access_token": PAGE_ACCESS_TOKEN}
        payload = {
            "recipient": {"id": sender_id},
            "message": {"text": message}
        }
        r = requests.post(url, params=params, json=payload)
        print("SEND STATUS:", r.status_code)
    except Exception as e:
        print("SEND ERROR:", e)

# ===== RENDER PORT CONFIG =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
