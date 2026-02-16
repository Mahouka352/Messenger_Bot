import os
import requests
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

# ====== LOAD ENV ======
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

# ====== CONFIG GEMINI ======
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ====== VERIFY WEBHOOK ======
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge
    return "Invalid verification token", 403


# ====== HANDLE MESSAGE ======
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]

                if "message" in messaging_event and "text" in messaging_event["message"]:
                    user_message = messaging_event["message"]["text"]

                    # ==== Gọi Gemini ====
                    try:
                        response = model.generate_content(user_message)
                        ai_reply = response.text
                    except Exception as e:
                        print("Gemini error:", e)
                        ai_reply = "Xin lỗi, hiện tại AI đang lỗi."

                    send_message(sender_id, ai_reply)

    return "OK", 200


# ====== SEND MESSAGE TO FB ======
def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    requests.post(url, json=payload)


# ====== ROOT TEST ======
@app.route("/")
def home():
    return "Bot Messenger + Gemini đang chạy"


if __name__ == "__main__":
    app.run(debug=True)
