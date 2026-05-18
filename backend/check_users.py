from pymongo import MongoClient

from app.config import MONGO_URI


if not MONGO_URI or MONGO_URI == "mongodb://localhost:27017":
    raise RuntimeError("MONGO_URI is not configured")


client = MongoClient(MONGO_URI)
db = client['memoryvault_db']

users = list(db['users'].find({}, {'email': 1, 'name': 1}))
print(f'Total users: {len(users)}')
print('\nUsers:')
for u in users:
    print(f"  Name: {u.get('name')}")
    print(f"  Email: {u.get('email')}")
    print()
