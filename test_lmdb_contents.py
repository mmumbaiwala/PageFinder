from lmdb_document_store import LmdbDocumentStore


def test_database_contents(db_path: str = "document_store.lmdb"):
    """Test and display contents of the LMDB database."""
    try:
        db = LmdbDocumentStore(db_path)
        
        # List all documents
        docs = db.list_all_docs()
        print(f"Documents in database: {docs}")
        
        if not docs:
            print("No documents found in database")
            return
        
        # Show details for each document
        for doc_id in docs:
            print(f"\n=== Document: {doc_id} ===")
            
            # Get metadata
            metadata = db.get_document_metadata(doc_id)
            if metadata:
                print(f"File: {metadata['file_name']}")
                print(f"Path: {metadata['file_path']}")
                print(f"Pages: {metadata['page_count']}")
                print(f"Size: {metadata['file_size']} bytes")
                print(f"Processed: {metadata['processing_date']}")
            
            # Get page texts (show first few pages as example)
            print("\nPage contents (first 3 pages):")
            for page_num in range(1, min(4, metadata['page_count'] + 1)):
                digital_text = db.get_page_digital_text(doc_id, page_num)
                ocr_text = db.get_page_ocr_text(doc_id, page_num)
                
                print(f"\n  Page {page_num}:")
                if digital_text:
                    print(f"    Digital text: {digital_text[:100]}{'...' if len(digital_text) > 100 else ''}")
                if ocr_text:
                    print(f"    OCR text: {ocr_text[:100]}{'...' if len(ocr_text) > 100 else ''}")
        
        db.close()
        
    except Exception as e:
        print(f"Error accessing database: {e}")


if __name__ == "__main__":
    test_database_contents()
