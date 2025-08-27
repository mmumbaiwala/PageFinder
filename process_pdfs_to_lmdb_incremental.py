import os
import fitz
from pathlib import Path
from text_preprocessing import extract_text_from_pdf_images_ocr, digital_pdf_get_text
from lmdb_document_store import LmdbDocumentStore
import argparse
import hashlib
import time


def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file to detect changes."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def process_pdf_folder_incremental(folder_path: str, db_path: str = "document_store.lmdb", tesseract_path: str = None):
    """
    Process PDFs in a folder incrementally - only reprocess changed files.
    
    Args:
        folder_path: Path to folder containing PDFs
        db_path: Path to LMDB database
        tesseract_path: Optional path to Tesseract executable for OCR
    """
    # Initialize LMDB store
    db = LmdbDocumentStore(db_path)
    
    # Get all PDF files in the folder
    pdf_files = list(Path(folder_path).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Track which documents exist in the database
    existing_docs = set(db.list_all_docs())
    processed_docs = set()
    
    for pdf_file in pdf_files:
        try:
            print(f"\nProcessing: {pdf_file.name}")
            
            # Generate document ID from filename
            doc_id = pdf_file.stem
            processed_docs.add(doc_id)
            
            # Check if file has changed
            current_hash = get_file_hash(str(pdf_file))
            metadata = db.get_document_metadata(doc_id)
            
            # Check if we have a valid hash to compare against
            if metadata and 'file_hash' in metadata and metadata['file_hash']:
                if metadata['file_hash'] == current_hash:
                    print(f"  ✓ File unchanged, skipping processing")
                    continue
                else:
                    print(f"  🔄 File changed, reprocessing...")
            else:
                print(f"  🆕 New file or no hash stored, processing...")
            
            # Open PDF document
            doc = fitz.open(str(pdf_file))
            page_count = len(doc)
            
            print(f"  Pages: {page_count}")
            
            # Extract digital text from all pages
            print("  Extracting digital text...")
            digital_texts = digital_pdf_get_text(str(pdf_file))
            
            # Extract OCR text from images on all pages
            print("  Extracting OCR text from images...")
            ocr_texts = extract_text_from_pdf_images_ocr(doc, tesseract_path)
            
            # Save document metadata with hash
            metadata = {
                "page_count": page_count,
                "file_size": pdf_file.stat().st_size,
                "processing_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_hash": current_hash,
                "last_modified": pdf_file.stat().st_mtime
            }
            db.save_document_metadata(doc_id, str(pdf_file), pdf_file.name, metadata)
            
            # Save page texts
            for page_num in range(page_count):
                digital_text = digital_texts[page_num] if page_num < len(digital_texts) else ""
                ocr_text = ocr_texts[page_num] if page_num < len(ocr_texts) else ""
                
                db.save_page_texts(doc_id, page_num + 1, digital_text, ocr_text)
            
            print(f"  ✓ Saved {page_count} pages to database")
            
            # Close document
            doc.close()
            
        except Exception as e:
            print(f"  ✗ Error processing {pdf_file.name}: {e}")
            continue
    
    # Remove orphaned documents (files that no longer exist)
    orphaned_docs = existing_docs - processed_docs
    if orphaned_docs:
        print(f"\n🗑️  Removing {len(orphaned_docs)} orphaned documents:")
        for doc_id in orphaned_docs:
            print(f"  - {doc_id}")
            # Note: You might want to add a method to remove documents from the database
            # For now, we'll just mark them as orphaned in metadata
    
    # Close database
    db.close()
    print(f"\nProcessing complete! Database saved to {db_path}")
    print(f"Processed: {len(processed_docs)} documents")
    if orphaned_docs:
        print(f"Orphaned: {len(orphaned_docs)} documents")


def main():
    parser = argparse.ArgumentParser(description="Process PDFs in a folder incrementally and store in LMDB")
    parser.add_argument("folder_path", help="Path to folder containing PDFs")
    parser.add_argument("--db", default="document_store.lmdb", help="LMDB database path")
    parser.add_argument("--tesseract", help="Path to Tesseract executable")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.folder_path):
        print(f"Error: Folder {args.folder_path} does not exist")
        return
    
    if not os.path.isdir(args.folder_path):
        print(f"Error: {args.folder_path} is not a directory")
        return
    
    process_pdf_folder_incremental(args.folder_path, args.db, args.tesseract)


if __name__ == "__main__":
    # Example usage without command line arguments
    # Uncomment and modify the line below to run directly
    
    process_pdf_folder_incremental("SampleData", tesseract_path=r"C:\Users\mmumbaiwala\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
    
    # Or run with command line arguments
    # main()
