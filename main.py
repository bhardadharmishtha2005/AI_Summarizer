import fitz  # PyMuPDF
import os
import sys
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Fix path issue on Vercel
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Load .env
load_dotenv()

# Gemini API Key
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=API_KEY)

# FastAPI app
app = FastAPI()

# CORS Fix
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini Summary Function
def generate_professional_summary(text_content):
    try:
        # Stable Gemini Model
        model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(
            f"""
            Write a professional, clear, human-like summary of the following content.

            Content:
            {text_content[:4000]}
            """
        )

        return response.text

    except Exception as e:
        return f"Gemini Error: {str(e)}"


# API Route
@app.post("/summarize")
async def handle_request(
    text: str = Form(None),
    file: UploadFile = File(None)
):
    final_text = ""

    # PDF Upload Support
    if file and file.filename.endswith(".pdf"):
        pdf_data = await file.read()

        doc = fitz.open(stream=pdf_data, filetype="pdf")

        for page in doc:
            final_text += page.get_text()

        doc.close()

    # Text Input Support
    elif text:
        final_text = text

    # Empty Input Check
    if not final_text.strip():
        return {
            "summary": "No valid content provided for analysis."
        }

    # Generate Summary
    summary = generate_professional_summary(final_text)

    return {
        "summary": summary
    }


# Local Run
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)