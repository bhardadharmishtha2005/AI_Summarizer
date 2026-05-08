import fitz
import requests
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# =========================
# Load ENV
# =========================
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# =========================
# FastAPI App
# =========================
app = FastAPI()

# =========================
# CORS Configuration
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Gemini API Function
# =========================
import time # Add this at the top with other imports

def generate_summary(prompt):
    model_id = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_id}:generateContent?key={API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    # Try up to 3 times if the server is busy
    for attempt in range(3):
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if response.status_code == 200:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        
        # If the server is busy (503), wait 2 seconds and try again
        elif response.status_code == 503:
            print(f"Server busy, retrying attempt {attempt + 1}...")
            time.sleep(2)
            continue
        else:
            return f"Error: {str(result)}"

    return "Server is currently too busy. Please try again in a few minutes."

# =========================
# API Route
# =========================
@app.post("/summarize")
async def summarize_content(
    text: str = Form(None),
    file: UploadFile = File(None),
    length: str = Form("medium")
):
    content = ""

    # 1. Handle PDF Extraction
    if file and file.filename.endswith(".pdf"):
        try:
            pdf_bytes = await file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                content += page.get_text()
            doc.close()
        except Exception as e:
            return {"summary": f"PDF Error: {str(e)}"}
    elif text:
        content = text

    # 2. Validation
    if not content.strip():
        return {"summary": "No content found."}

    # 3. Content Truncation (Safety for long documents)
    content = content[:3000]

    # 4. Prompt Engineering
    if length == "short":
        prompt = f"Summarize this in 5 concise bullet points:\n\n{content}"
    elif length == "long":
        prompt = f"Provide a detailed, comprehensive summary of the following:\n\n{content}"
    else:
        prompt = f"Provide a professional medium-length summary of the following:\n\n{content}"

    # 5. Generate and Return
    try:
        summary = generate_summary(prompt)
        return {"summary": summary}
    except Exception as e:
        return {"summary": f"Gemini API Error: {str(e)}"}

# =========================
# Run Server
# =========================
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)