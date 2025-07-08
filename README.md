# 🧾 API Document Validator (OCR + PDF)

This service allows users to upload scanned documents (PDFs or images), and validates them based on expected keywords for document types such as:

- UMID / PhilID
- Business Permit
- Articles of Incorporation
- DTI License
- BIR Form
- Driver’s License, Passport, TIN, etc.

Uses `pytesseract` and `pdfplumber` to extract and analyze content.

---

## 📦 Features

- 🧠 Smart keyword detection per document type
- 🖼 Supports PNG, JPG, JPEG, and PDF files
- 📏 Upload size limited to 20MB
- 🐳 Dockerized for easy deployment

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/fastapi-doc-validator.git
cd fastapi-doc-validator
```

### 2. Create requirements.txt
```bash
fastapi
uvicorn[standard]
pytesseract
pdfplumber
pillow
```

## 🐳 Run with Docker

### 1. Build the Docker image
```bash
docker build -t fastapi-doc-validator .
```

### 2. Run the container
```bash
docker run -p 8000:8000 fastapi-doc-validator
```

### 🌐 Deployment Options
 - Deploy to any Docker host: DigitalOcean, AWS EC2, Render, Railway
 - Push this image to Docker Hub or use in a CI/CD pipeline
 - For Render or Railway: Use uvicorn main:app --host 0.0.0.0 --port 10000 as start command

## 🧪 Test the API

### Using curl:
```bash
curl -X POST http://localhost:8000/validate-file \
  -F "type=sss-gsis-umid" \
  -F "file=@/full/path/to/your-id.pdf"
```

### Or open Swagger UI:
```bash
http://localhost:8000/docs
```

## 🔍 Supported type values

| Type Key                    | Description                      |
| --------------------------- | -------------------------------- |
| `sss-gsis-umid`             | Unified Multi-Purpose ID         |
| `philid`                    | Philippine ID                    |
| `business-permit`           | Local Business Permit            |
| `articles-of-incorporation` | SEC Articles of Incorporation    |
| `dti-license`               | DTI Certificate                  |
| `bir-form`                  | BIR Form or Certificate          |
| `amended-gis`               | Amended General Info Sheet (GIS) |
| `sec`                       | SEC Certificate                  |
| `passport`                  | Philippine Passport              |
| `drivers-license`           | Driver's License                 |
| `tin-id`                    | TIN ID                           |

### 👨‍💻 Maintainer
 - Created by Alexis Michael Rizon.
 - For questions, contact [alexismichael2015@gmail.com].