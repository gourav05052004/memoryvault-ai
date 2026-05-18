import json

from pymongo import MongoClient

from app.config import MONGO_URI



if not MONGO_URI or MONGO_URI == "mongodb://localhost:27017":
    raise RuntimeError("MONGO_URI is not configured")


client = MongoClient(MONGO_URI)
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
