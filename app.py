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
genai.configure(api_key=G_
