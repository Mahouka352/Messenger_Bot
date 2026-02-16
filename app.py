import os
import requests
import google.generativeai as genai
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Lấy các biến môi trường
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Cấu hình Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route("/", methods=["GET"])
def home():
    return "Bot Gemini đang hoạt động!", 200

@app.route("/webhook", methods=["GET"])
def verify():
    # Xác thực với Facebook Webhook
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Xác thực thất bại", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                if "message" in messaging and "text" in messaging["message"]:
                    user_text = messaging["message"]["text"]
                    
                    # Gọi Gemini để lấy câu trả lời
                    ai_reply = ask_gemini(user_text)
                    
                    # Gửi câu trả lời lại cho khách
                    send_fb_message(sender_id, ai_reply)
    return "OK", 200

def ask_gemini(prompt):
    try:
        # Bạn có thể đổi câu lệnh hệ thống ở đây để bot trả lời theo ý muốn
        full_prompt = f"Bạn là một trợ lý bán hàng thân thiện. Trả lời ngắn gọn câu hỏi này: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text if response.text else "Mình chưa nghĩ ra câu trả lời..."
    except Exception as e:
        print(f"Lỗi Gemini: {e}")
        return "Hệ thống AI đang bận, bạn vui lòng nhắn lại sau nhé!"

def send_fb_message(sender_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": message_text}
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    # Fix lỗi Port Binding trên Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
