import os
import fitz
from pathlib import Path
from text_preprocessing import extract_text_from_pdf_images_ocr, extract_text_from_pdf_digital
from lmdb_document_store import LmdbDocumentStore
import argparse
import hashlib
from tqdm import tqdm


def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file to detect changes."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def process_pdf_folder(folder_path: str, db_path: str = "document_store.lmdb", tesseract_path: str = None):
    """
    Process all PDFs in a folder and store them in LMDB datastore.
    
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
    
    # Create progress bar
    with tqdm(total=len(pdf_files), desc="Processing PDFs", unit="file") as pbar:
        for pdf_file in pdf_files:
            try:
                # Update progress bar description to show current file
                pbar.set_description(f"Processing: {pdf_file.name}")
                
                # Generate document ID from filename
                doc_id = pdf_file.stem
                
                # Open PDF document
                doc = fitz.open(str(pdf_file))
                page_count = len(doc)
                
                print(f"  Pages: {page_count}")
                
                # Extract digital text from all pages
                print("  Extracting digital text...")
                digital_texts = extract_text_from_pdf_digital(str(pdf_file))
                
                # Extract OCR text from images on all pages
                print("  Extracting OCR text from images...")
                ocr_texts = extract_text_from_pdf_images_ocr(doc, tesseract_path)
                
                # Save document metadata
                metadata = {
                    "page_count": page_count,
                    "file_size": pdf_file.stat().st_size,
                    "processing_date": str(Path().cwd()),
                    "file_hash": get_file_hash(str(pdf_file)),  # Add file hash for compatibility
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
            finally:
                # Always update progress bar, even if there was an error
                pbar.update(1)
    
    # Close database
    db.close()
    print(f"\nProcessing complete! Database saved to {db_path}")


def main():
    parser = argparse.ArgumentParser(description="Process PDFs in a folder and store in LMDB")
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
    
    process_pdf_folder(args.folder_path, args.db, args.tesseract)


if __name__ == "__main__":
    # Example usage without command line arguments
    # Uncomment and modify the line below to run directly
    
    process_pdf_folder("SampleData", tesseract_path=r"C:\Users\mmumbaiwala\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
    
    # Or run with command line arguments
    # main()
