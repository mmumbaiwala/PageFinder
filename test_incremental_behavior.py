import os
import hashlib
from pathlib import Path
from lmdb_document_store import LmdbDocumentStore


def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file to detect changes."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def test_incremental_behavior():
    """Test the incremental behavior by showing file hashes and database state."""
    
    # Check current database
    print("=== CURRENT DATABASE STATE ===")
    try:
        db = LmdbDocumentStore("document_store.lmdb")
        docs = db.list_all_docs()
        print(f"Documents in database: {docs}")
        
        for doc_id in docs:
            metadata = db.get_document_metadata(doc_id)
            if metadata:
                print(f"\nDocument: {doc_id}")
                print(f"  File hash: {metadata.get('file_hash', 'NOT SET')}")
                print(f"  Processing date: {metadata.get('processing_date', 'NOT SET')}")
                print(f"  File size: {metadata.get('file_size', 'NOT SET')}")
        
        db.close()
    except Exception as e:
        print(f"Database error: {e}")
    
    # Check current files
    print("\n=== CURRENT FILES IN SAMPLE DATA ===")
    pdf_files = list(Path("SampleData").glob("*.pdf"))
    
    for pdf_file in pdf_files:
        current_hash = get_file_hash(str(pdf_file))
        file_size = pdf_file.stat().st_size
        modified_time = pdf_file.stat().st_mtime
        
        print(f"\nFile: {pdf_file.name}")
        print(f"  Current hash: {current_hash}")
        print(f"  File size: {file_size} bytes")
        print(f"  Modified: {modified_time}")
    
    # Test change detection
    print("\n=== CHANGE DETECTION TEST ===")
    try:
        db = LmdbDocumentStore("document_store.lmdb")
        
        for pdf_file in pdf_files:
            doc_id = pdf_file.stem
            current_hash = get_file_hash(str(pdf_file))
            metadata = db.get_document_metadata(doc_id)
            
            print(f"\nFile: {pdf_file.name}")
            if metadata and 'file_hash' in metadata:
                stored_hash = metadata['file_hash']
                if current_hash == stored_hash:
                    print(f"  ✓ UNCHANGED - Hash matches: {current_hash[:8]}...")
                else:
                    print(f"  🔄 CHANGED - Stored: {stored_hash[:8]}... vs Current: {current_hash[:8]}...")
            else:
                print(f"  🆕 NEW - No hash stored, will process")
        
        db.close()
    except Exception as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    test_incremental_behavior()
