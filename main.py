from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image, ImageOps
import pdfplumber
import io
import re
import tempfile
import os

app = FastAPI()

# Middleware: Limit upload size to 20MB
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    max_body_size = 20 * 1024 * 1024
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_body_size:
        return JSONResponse(status_code=413, content={"detail": "File too large. Max 20 MB allowed."})
    return await call_next(request)

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
        for i, page in enumerate(pdf.pages):
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

# 🧠 Keyword map per document type
DOCUMENT_KEYWORDS = {
    "sss-gsis-umid": ["unified multi-purpose id", "multi-purpose", "pambansang pagkakakilanlan", "philippine identification card", "gsis", "sss"],
    "philid": ["philippine identification card", "pambansang pagkakakilanlan"],
    "business-permit": ["business permit"],
    "articles-of-incorporation": ["articles of incorporation", "incorporated"],
    "dti-license": ["department of trade and industry", "dti certificate"],
    "bir-form": ["bir form", "bureau of internal revenue"],
    "amended-gis": ["amended general information sheet", "amended gis"],
    "sec": ["securities and exchange commission"],
    "passport": ["passport", "republic of the philippines passport"],
    "drivers-license": ["driver's license", "dln"],
    "tin-id": ["taxpayer identification number", "tin id"]
}

@app.post("/validate-file")
async def verify_file(type: str = Form(...), file: UploadFile = File(...)):
    try:
        if type not in DOCUMENT_KEYWORDS:
            raise HTTPException(status_code=400, detail="Unsupported document type")

        raw_text = process_file(file)
        normalized_text = normalize_text(raw_text)

        # Check for any matching keyword
        keywords = DOCUMENT_KEYWORDS[type]
        found_keyword = next((kw for kw in keywords if kw in normalized_text), None)

        return JSONResponse(content={
            "is_valid": bool(found_keyword),
            "message": f"\"{found_keyword}\" detected." if found_keyword else "No expected keyword found.",
            "debug_text_snippet": normalized_text[:1000]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
