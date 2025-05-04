#memory/mongo_client.py
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "debate_engine"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]