import fitz
import os
import sys

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

# Summary Function
def generate_professional_summary(text_content):

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
            Write a professional, human-like summary
            of the following content:

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