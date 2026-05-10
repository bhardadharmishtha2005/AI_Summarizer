import fitz  # PyMuPDF for PDF extraction
import requests
import os
import time
import sys
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure system path is correct for Vercel environments
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()

# Fixes the 'Forbidden' connection error in your logs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_professional_summary(text_content):
    # This is the exact production URL for Gemini 1.5 Flash
    # This uses the 'latest' alias which is the most stable way to avoid 404 errors
    # This uses the 'latest' alias which is the most stable way to avoid 404 errors
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
    
    # The payload MUST be in this exact nested structure
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Summarize this text like a human expert: {text_content[:4000]}"
            }]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        
        # If this still returns 404, we will see the EXACT reason here
        if response.status_code != 200:
            return f"Technical Error {response.status_code}: {response.text}"
            
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Connection Error: {str(e)}"

@app.post("/summarize")
async def handle_request(text: str = Form(None), file: UploadFile = File(None)):
    final_text = ""
    
    # Support for both manual text and PDF uploads
    if file and file.filename.endswith(".pdf"):
        pdf_data = await file.read()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        for page in doc:
            final_text += page.get_text()
        doc.close()
    elif text:
        final_text = text

    if not final_text.strip():
        return {"summary": "No valid content provided for analysis."}

    summary = generate_professional_summary(final_text)
    return {"summary": summary}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)