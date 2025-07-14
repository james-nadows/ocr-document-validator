from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.models import Response
from fastapi.openapi.utils import get_openapi
from typing import List
import pytesseract
from PIL import Image, ImageOps
import pdfplumber
import io
import tempfile
import os
import re

app = FastAPI(
    title="📄 API Document Validator (OCR + PDF)",
    description="""
This service allows users to upload scanned documents (PDFs or images), 
and validates them based on expected keywords for document types like:

- UMID / PhilID
- Business Permit
- Articles of Incorporation
- DTI License
- BIR Form
- Passport, Driver’s License, TIN ID, etc.
""",
    version="1.0.0"
)

DOCUMENT_KEYWORDS = {
    105: ["unified multi-purpose id", "pambansang pagkakakilanlan", "philippine identification card", "gsis", "sss"],
    103: ["passport", "republic of the philippines passport"],
    104: ["driver's license", "dln"],
    102: ["business permit"],
    106: ["taxpayer identification number", "tin id"],
    123: ["articles of incorporation", "incorporated"],
    124: ["license", "permit", "business permit"],
    125: ["general information sheet", "gis"],
    126: ["securities and exchange commission", "certificate of incorporation"],
    127: ["bureau of internal revenue", "bir form"],
    129: [
            "unified multi-purpose id", 
            "pambansang pagkakakilanlan", 
            "philippine identification card", 
            "gsis", 
            "sss", 
            "passport", 
            "identification", 
            "driver's license", 
            "dln"
        ],
}

def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).lower()

def preprocess_image(path: str):
    image = Image.open(path)
    image = image.convert("L")
    image = ImageOps.autocontrast(image)
    image = image.resize((image.width * 2, image.height * 2))
    return image

def extract_text_from_image(path: str) -> str:
    image = preprocess_image(path)
    return pytesseract.image_to_string(image)

def extract_text_from_pdf(path: str) -> str:
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            else:
                image = page.to_image(resolution=300).original
                text += pytesseract.image_to_string(image) + "\n"
    return text

def process_file(file: UploadFile) -> str:
    ext = file.filename.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    try:
        if ext.endswith(('.png', '.jpg', '.jpeg')):
            return extract_text_from_image(tmp_path)
        elif ext.endswith('.pdf'):
            return extract_text_from_pdf(tmp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
    finally:
        os.remove(tmp_path)

@app.post(
    "/validate-file",
    summary="Validate Uploaded Document",
    description="Upload a document (image or PDF) and specify the type to validate its authenticity based on detected keywords.",
    response_description="Validation result with keyword detection details.",
)
async def validate_file(
    type: int = Form(..., description="Document type ID"),
    file: UploadFile = File(..., description="PDF or image file to be validated")
):
    """
    Validates document content by checking expected keywords based on its type.
    """
    try:
        if type not in DOCUMENT_KEYWORDS:
            raise HTTPException(status_code=400, detail="Unsupported document type")

        raw_text = process_file(file)
        normalized_text = normalize_text(raw_text)
        keywords = DOCUMENT_KEYWORDS[type]
        found_keyword = next((kw for kw in keywords if kw in normalized_text), None)

        return JSONResponse(content={
            "is_valid": bool(found_keyword),
            "message": f"\"{found_keyword}\" detected." if found_keyword else "No expected keyword found.",
            "debug_text_snippet": normalized_text[:1000]
        })
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
