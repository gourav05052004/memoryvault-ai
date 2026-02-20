from pymongo import MongoClient

client = MongoClient('mongodb+srv://11f15gouravkumarsonu_db_user:4sRt7rmxadzvFnnA@cluster0.jempbxy.mongodb.net/?appName=Cluster0')
db = client['memoryvault_db']

pdfs = list(db['memories'].find({'type': 'pdf'}).limit(1))

if pdfs:
    pdf = pdfs[0]
    print("PDF Info:")
    print(f"Title: {pdf.get('title')}")
    print(f"Resource Type: {pdf.get('resourceType')}")
    print(f"Public ID: {pdf.get('publicId')}")
    print(f"File URL: {pdf.get('fileUrl')}")
