import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def get_db():
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")

    if not mongo_uri:
        raise RuntimeError("MONGO_URI is missing. Create a .env file based on env.example.")
    if not db_name:
        raise RuntimeError("MONGO_DB_NAME is missing. Create a .env file based on env.example.")

    client = MongoClient(mongo_uri)
    return client[db_name]