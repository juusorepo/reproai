from dotenv import load_dotenv
import os
from pymongo import MongoClient
from pprint import pprint

def main():
    # Load environment variables
    load_dotenv()
    
    # Connect to MongoDB
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client.manuscript_db
    
    # Get all manuscripts
    print("\nAll manuscripts in database:")
    print("-" * 50)
    for doc in db.manuscripts.find():
        pprint(doc)
    
    # Get collection stats
    print("\nCollection information:")
    print("-" * 50)
    print(f"Number of documents: {db.manuscripts.count_documents({})}")
    print(f"Indexes: {db.manuscripts.index_information()}")

if __name__ == "__main__":
    main()
