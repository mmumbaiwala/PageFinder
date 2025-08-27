from lmdb_document_store import LmdbDocumentStore
import pandas as pd


def quick_lmdb_view(db_path: str = "document_store.lmdb"):
    """
    Quick view of LMDB database contents in the terminal.
    
    Args:
        db_path: Path to LMDB database
    """
    try:
        db = LmdbDocumentStore(db_path)
        
        # Get all documents
        docs = db.list_all_docs()
        
        if not docs:
            print("No documents found in database")
            return
        
        print(f"📚 Database contains {len(docs)} documents")
        print("=" * 80)
        
        # Document overview table
        overview_data = []
        for doc_id in docs:
            metadata = db.get_document_metadata(doc_id)
            if metadata:
                overview_data.append({
                    'Document ID': doc_id,
                    'File Name': metadata.get('file_name', 'N/A'),
                    'Pages': metadata.get('page_count', 'N/A'),
                    'Size (KB)': round(metadata.get('file_size', 0) / 1024, 1) if metadata.get('file_size') else 'N/A',
                    'Hash': metadata.get('file_hash', 'N/A')[:12] + '...' if metadata.get('file_hash') else 'N/A'
                })
        
        overview_df = pd.DataFrame(overview_data)
        print("\n📋 Document Overview:")
        print(overview_df.to_string(index=False))
        
        # Page-level summary
        print("\n📄 Page-Level Summary:")
        page_summary = []
        for doc_id in docs:
            metadata = db.get_document_metadata(doc_id)
            if metadata and 'page_count' in metadata:
                for page_num in range(1, metadata['page_count'] + 1):
                    digital_text = db.get_page_digital_text(doc_id, page_num) or ""
                    ocr_text = db.get_page_ocr_text(doc_id, page_num) or ""
                    
                    page_summary.append({
                        'Doc ID': doc_id[:15] + '...' if len(doc_id) > 15 else doc_id,
                        'Page': page_num,
                        'Digital': len(digital_text),
                        'OCR': len(ocr_text),
                        'Total': len(digital_text) + len(ocr_text)
                    })
        
        page_df = pd.DataFrame(page_summary)
        print(page_df.to_string(index=False))
        
        # Quick statistics
        print("\n📊 Quick Statistics:")
        total_pages = sum(metadata.get('page_count', 0) for doc_id in docs if (metadata := db.get_document_metadata(doc_id)))
        total_digital = sum(len(db.get_page_digital_text(doc_id, page_num) or "") 
                          for doc_id in docs 
                          for page_num in range(1, (db.get_document_metadata(doc_id) or {}).get('page_count', 0) + 1))
        total_ocr = sum(len(db.get_page_ocr_text(doc_id, page_num) or "") 
                       for doc_id in docs 
                       for page_num in range(1, (db.get_document_metadata(doc_id) or {}).get('page_count', 0) + 1))
        
        print(f"  Total Pages: {total_pages}")
        print(f"  Total Digital Text: {total_digital:,} characters")
        print(f"  Total OCR Text: {total_ocr:,} characters")
        print(f"  Total Text: {total_digital + total_ocr:,} characters")
        print(f"  Average Pages per Doc: {round(total_pages / len(docs), 1)}")
        
        db.close()
        
    except Exception as e:
        print(f"Error viewing database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    quick_lmdb_view()
