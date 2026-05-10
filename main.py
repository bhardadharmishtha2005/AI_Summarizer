import fitz
import os
import sys
import requests
from google import genai

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Fix path for Vercel
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Load environment variables
load_dotenv()

# API Key
API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini Client
client = genai.Client(api_key=API_KEY)

# FastAPI App
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_professional_summary(text_content):
    # This specific 'v1beta' URL with 'gemini-1.5-flash' is the most reliable for new free keys
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Provide a professional, human-like summary of this text: {text_content[:4000]}"
            }]
        }]
    }
    
    try:
        # Increased timeout to 30s to handle free-tier slow responses
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # If this still fails, it will tell us the EXACT reason (e.g. Quota vs Key)
            return f"Service Notification: {response.status_code}. {response.text}"
            
    except Exception as e:
        return f"Connection Insight: {str(e)}"


# API Route
@app.post("/summarize")

async def handle_request(
    text: str = Form(None),
    file: UploadFile = File(None)
):

    final_text = ""

    # PDF Upload
    if file and file.filename.endswith(".pdf"):

        pdf_data = await file.read()

        doc = fitz.open(
            stream=pdf_data,
            filetype="pdf"
        )

        for page in doc:
            final_text += page.get_text()

        doc.close()

    # Text Input
    elif text:

        final_text = text

    # Empty Check
    if not final_text.strip():

        return {
            "summary":
            "No valid content provided."
        }

    # Generate Summary
    summary = generate_professional_summary(
        final_text
    )

    return {
        "summary": summary
    }


# Local Run
if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )