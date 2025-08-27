from lmdb_document_store import LmdbDocumentStore
import pickle

def debug_metadata():
    """Debug the metadata saving and retrieval."""
    
    # Test basic functionality
    print("=== TESTING METADATA FUNCTIONS ===")
    
    try:
        # Create a test database
        db = LmdbDocumentStore("test_debug.lmdb")
        
        # Test data
        test_metadata = {
            "page_count": 5,
            "file_size": 12345,
            "processing_date": "2024-01-01 12:00:00",
            "file_hash": "test_hash_123",
            "last_modified": 1234567890.0
        }
        
        print(f"Test metadata: {test_metadata}")
        
        # Save metadata
        print("\nSaving metadata...")
        db.save_document_metadata("test_doc", "/test/path.pdf", "test.pdf", test_metadata)
        print("✓ Metadata saved")
        
        # Retrieve metadata
        print("\nRetrieving metadata...")
        retrieved = db.get_document_metadata("test_doc")
        print(f"Retrieved: {retrieved}")
        
        if retrieved:
            print(f"Keys in retrieved: {list(retrieved.keys())}")
            for key, value in retrieved.items():
                print(f"  {key}: {value}")
        
        db.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_metadata()
