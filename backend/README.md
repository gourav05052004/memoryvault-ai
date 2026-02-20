# MemoryVault AI Backend

## Environment variables

Create/update `backend/.env` with:

```
MONGO_URI="your_mongodb_uri"
GROQ_API_KEY="your_groq_api_key"
GROQ_CHAT_MODEL="llama-3.3-70b-versatile"
GROQ_EMBEDDING_MODEL="text-embedding-3-small"
TESSERACT_CMD="C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
JWT_SECRET_KEY="change-this-in-production"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES="60"
```

`GROQ_API_KEY` is required for summary/tag generation and ask responses.

## Run

From `backend/`:

```
pip install "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt==4.0.1"
python -m uvicorn app.main:app --reload --port 8001
```
