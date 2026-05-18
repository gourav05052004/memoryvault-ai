from pymongo import MongoClient

from app.config import MONGO_URI


if not MONGO_URI or MONGO_URI == "mongodb://localhost:27017":
    raise RuntimeError("MONGO_URI is not configured")


client = MongoClient(MONGO_URI)
db = client['memoryvault_db']

pdfs = list(db['memories'].find({'type': 'pdf'}).limit(1))

if pdfs:
    pdf = pdfs[0]
    print("PDF Info:")
    print(f"Title: {pdf.get('title')}")
    print(f"Resource Type: {pdf.get('resourceType')}")
    print(f"Public ID: {pdf.get('publicId')}")
    print(f"File URL: {pdf.get('fileUrl')}")
