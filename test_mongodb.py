from dotenv import load_dotenv
import os
from pymongo import MongoClient

def test_mongodb_connection():
    load_dotenv()
    
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv("MONGODB_URI")
    print("Testing MongoDB connection...")
    
    try:
        # Create client
        client = MongoClient(mongodb_uri)
        
        # Test connection by listing databases
        dbs = client.list_database_names()
        print("Successfully connected to MongoDB!")
        print("Available databases:", dbs)
        
        # Test specific database operations
        db = client.reproai
        print("\nCollections in reproai database:", db.list_collection_names())
        
    except Exception as e:
        print("Error connecting to MongoDB:", str(e))
    
if __name__ == "__main__":
    test_mongodb_connection()
