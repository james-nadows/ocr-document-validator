from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image, ImageOps
import pdfplumber
import io
import re

app = FastAPI()

def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).lower()

def preprocess_image(file_bytes: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(file_bytes))
    image = image.convert("L")  # grayscale
    image = ImageOps.autocontrast(image)
    image = image.resize((image.width * 2, image.height * 2))
    return image

def extract_text_from_image(file_bytes: bytes) -> str:
    image = preprocess_image(file_bytes)
    return pytesseract.image_to_string(image)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                print(f"📝 Page {i+1} Text:\n{page_text}")
                text += page_text + "\n"
            else:
                # Fallback: OCR the rendered image of the page
                print(f"⚠️ Page {i+1} has no extractable text. Trying OCR.")
                image = page.to_image(resolution=300).original
                ocr_text = pytesseract.image_to_string(image)
                print(f"🖼 OCR Text Page {i+1}:\n{ocr_text}")
                text += ocr_text + "\n"
    return text

@app.post("/verify-articles-of-incorporation")
async def verify_document(file: UploadFile = File(...)):
    ext = file.filename.lower()
    file_bytes = await file.read()

    try:
        # Step 1: Extract raw text
        if ext.endswith(('.png', '.jpg', '.jpeg')):
            raw_text = extract_text_from_image(file_bytes)
        elif ext.endswith('.pdf'):
            raw_text = extract_text_from_pdf(file_bytes)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        # Step 2: Normalize and match
        normalized_text = normalize_text(raw_text)
        found = "articles of" in normalized_text

        # Step 3: Return with debug text
        return JSONResponse(content={
            "is_valid": found,
            "message": "\"Articles of\" detected." if found else "\"Articles of\" not found.",
            "debug_text_snippet": normalized_text[:1000]  # return partial extracted text
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
