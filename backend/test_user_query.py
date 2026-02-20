from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['memoryvault-ai']
users = db['users']

# Find user by email
user = users.find_one({'email': '11f15.gouravkumarsonu@gmail.com'})
if user:
    print('User found:')
    print(f'  ID: {user.get("_id")}')
    print(f'  Name: "{user.get("name")}"')
    print(f'  Email: {user.get("email")}')
    print(f'  All fields: {user}')
else:
    print('User not found')

# Also list all users to see what's in the database
print('\nAll users in database:')
all_users = users.find()
for u in all_users:
    print(f'  - {u.get("email")}: name="{u.get("name")}"')
