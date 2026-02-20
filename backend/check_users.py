from pymongo import MongoClient

client = MongoClient('mongodb+srv://11f15gouravkumarsonu_db_user:4sRt7rmxadzvFnnA@cluster0.jempbxy.mongodb.net/?appName=Cluster0')
db = client['memoryvault_db']

users = list(db['users'].find({}, {'email': 1, 'name': 1}))
print(f'Total users: {len(users)}')
print('\nUsers:')
for u in users:
    print(f"  Name: {u.get('name')}")
    print(f"  Email: {u.get('email')}")
    print()
