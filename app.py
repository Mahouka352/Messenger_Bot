import os
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ===== VERIFY WEBHOOK =====
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403


# ===== RECEIVE MESSAGE =====
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if data["object"] == "page":
        for entry in data["entry"]:
            messaging = entry["messaging"][0]
            sender_id = messaging["sender"]["id"]

            if "message" in messaging and "text" in messaging["message"]:
                user_message = messaging["message"]["text"]

                ai_reply = ask_chatgpt(user_message)

                send_message(sender_id, ai_reply)

    return "OK", 200


# ===== CHATGPT FUNCTION =====
def ask_chatgpt(message):
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Bạn là trợ lý bán hàng chuyên nghiệp."},
                {"role": "user", "content": message}
            ]
        }

        response = requests.post(url, headers=headers, json=payload)
        result = response.json()

        return result["choices"][0]["message"]["content"]

    except Exception as e:
        print("OpenAI error:", e)
        return "Xin lỗi, hệ thống đang bận. Vui lòng thử lại sau."


# ===== SEND MESSAGE TO USER =====
def send_message(sender_id, message):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": message}
    }

    requests.post(url, json=payload)


if __name__ == "__main__":
    app.run(port=3000)
