import fitz  # PyMuPDF for PDF extraction [cite: 52]
import requests
import os
import time
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_professional_summary(text_content):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    
    # System instruction to ensure "Human-Like" output without AI labels
    prompt = f"""
    You are an expert executive assistant. Summarize the following text professionally.
    - Do not use robotic phrases like 'Here is a summary'.
    - Provide clear, insightful paragraphs.
    - Focus on core value points.
    - Ensure the tone is indistinguishable from a human expert.

    TEXT TO ANALYZE:
    {text_content[:4000]}
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # Retry logic for robust performance during the demo 
    for attempt in range(3):
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        elif response.status_code == 503:
            time.sleep(2)
            continue
    return "The system is currently refining its analysis. Please try again in a moment."

@app.post("/summarize")
async def handle_request(text: str = Form(None), file: UploadFile = File(None)):
    final_text = ""
    
    # Handle PDF and Text inputs [cite: 48, 50]
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