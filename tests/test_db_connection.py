"""Test MongoDB connection and inspect database structure."""
import streamlit as st
from pymongo import MongoClient
from pprint import pprint

def test_db_connection():
    """Test MongoDB connection and print collection info."""
    # Get MongoDB URI from Streamlit secrets
    mongodb_uri = st.secrets["MONGODB_URI"]
    if not mongodb_uri:
        print("Error: MONGODB_URI not found in Streamlit secrets")
        return
        
    print(f"\nTesting connection to: {mongodb_uri}")
    
    try:
        # Connect to MongoDB
        client = MongoClient(mongodb_uri)
        db = client.manuscript_db
        
        # Test connection
        client.admin.command('ping')
        print("[OK] Successfully connected to MongoDB")
        
        # Print database info
        print("\nCollections:")
        collections = db.list_collection_names()
        for coll in collections:
            count = db[coll].count_documents({})
            print(f"- {coll}: {count} documents")
            
        # Inspect compliance_summaries structure
        print("\nCompliance Summaries Structure:")
        summaries = list(db.compliance_summaries.find().limit(1))
        if summaries:
            summary = summaries[0]
            print("\nExample Summary Document:")
            pprint(summary)
            
            # Analyze structure
            print("\nDocument Structure:")
            def analyze_structure(obj, prefix=''):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        print(f"{prefix}- {key}: {type(value).__name__}")
                        if isinstance(value, (dict, list)):
                            analyze_structure(value, prefix + '  ')
                elif isinstance(obj, list) and obj:
                    print(f"{prefix}- (list of {len(obj)} items)")
                    analyze_structure(obj[0], prefix + '  ')
                            
            analyze_structure(summary)
        else:
            print("No compliance summaries found in database")
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    test_db_connection()
