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
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    payload = {"contents": [{"parts": [{"text": f"Summarize this professionally: {text_content[:4000]}"}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        # This will show you the REAL error in Vercel Logs
        if response.status_code != 200:
            print(f"API ERROR: {response.status_code} - {response.text}")
            return f"Error: The AI service returned status {response.status_code}. Check your API Key."
            
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"SYSTEM ERROR: {str(e)}")
        return "The system is currently refining its analysis. Please try again in a moment."

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