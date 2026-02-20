from pymongo import MongoClient
import json

client = MongoClient('mongodb+srv://11f15gouravkumarsonu_db_user:4sRt7rmxadzvFnnA@cluster0.jempbxy.mongodb.net/?appName=Cluster0')
db = client['memoryvault_db']

memories = list(db['memories'].find({'type': 'pdf'}).sort('createdAt', -1).limit(2))
print(f'PDF memories: {len(memories)}\n')

for m in memories:
    print(json.dumps({
        'title': m.get('title'),
        'type': m.get('type'),
        'fileName': m.get('fileName'),
        'publicId': m.get('publicId'),
        'resourceType': m.get('resourceType'),
        'fileUrl': str(m.get('fileUrl', 'N/A'))
    }, indent=2))
    print()
