import os
import google.generativeai as genai

# Load environment variables from the .env file

# Use the correct key name from your .env file
GEMINI_API_KEY = "AIzaSyA18g3XA4mkwBL2VEvXugoUTJYL1xSPUew"

# Fail-safe in case the key is missing
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is not set. Check your .env file.")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def call_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")  # or "gemini-pro" if needed
    response = model.generate_content(prompt)
    return response.text
