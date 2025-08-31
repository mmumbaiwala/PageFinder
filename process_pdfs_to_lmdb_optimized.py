import os
import fitz
from pathlib import Path
from text_preprocessing import extract_text_from_pdf_images_ocr, extract_text_from_pdf_digital
from lmdb_document_store import LmdbDocumentStore
import argparse
import hashlib
import time
import json
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from tqdm import tqdm
import psutil
import threading


class ProcessingConfig:
    """Configuration class for PDF processing optimization settings"""
    def __init__(self, **kwargs):
        self.max_workers = kwargs.get("max_workers", min(cpu_count(), 8))
        self.batch_size = kwargs.get("batch_size", 10)
        self.enable_ocr = kwargs.get("enable_ocr", True)
        self.enable_digital = kwargs.get("enable_digital", True)
        self.memory_limit_mb = kwargs.get("memory_limit_mb", 1024)
        self.skip_existing = kwargs.get("skip_existing", True)
        self.checkpoint_interval = kwargs.get("checkpoint_interval", 5)
        self.ocr_batch_size = kwargs.get("ocr_batch_size", 5)
        self.enable_caching = kwargs.get("enable_caching", True)


class FileHashCache:
    """Cache for file hashes to avoid recalculating"""
    def __init__(self, cache_file: str = ".file_hashes.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.lock = threading.Lock()
    
    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save hash cache: {e}")
    
    def get_hash(self, file_path: str) -> str:
        with self.lock:
            if file_path in self.cache:
                return self.cache[file_path]
            
            # Calculate hash and cache it
            hash_value = self._calculate_file_hash(file_path)
            self.cache[file_path] = hash_value
            self._save_cache()
            return hash_value
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file to detect changes."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


class ProcessingCheckpoint:
    """Checkpoint system for resuming interrupted processing"""
    def __init__(self, checkpoint_file: str = ".processing_checkpoint.json"):
        self.checkpoint_file = checkpoint_file
        self.checkpoint = self._load_checkpoint()
        self.lock = threading.Lock()
    
    def _load_checkpoint(self) -> dict:
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        
        return {
            "completed": [],
            "failed": [],
            "start_time": time.time(),
            "last_update": time.time()
        }
    
    def _save_checkpoint(self):
        try:
            self.checkpoint["last_update"] = time.time()
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.checkpoint, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save checkpoint: {e}")
    
    def mark_completed(self, file_name: str):
        with self.lock:
            if file_name not in self.checkpoint["completed"]:
                self.checkpoint["completed"].append(file_name)
                self._save_checkpoint()
    
    def mark_failed(self, file_name: str, error: str):
        with self.lock:
            self.checkpoint["failed"].append({
                "file": file_name,
                "error": error,
                "timestamp": time.time()
            })
            self._save_checkpoint()
    
    def is_completed(self, file_name: str) -> bool:
        return file_name in self.checkpoint["completed"]
    
    def get_stats(self) -> dict:
        return {
            "completed": len(self.checkpoint["completed"]),
            "failed": len(self.checkpoint["failed"]),
            "start_time": self.checkpoint.get("start_time"),
            "last_update": self.checkpoint.get("last_update")
        }


class MemoryMonitor:
    """Monitor memory usage and trigger cleanup when needed"""
    def __init__(self, memory_limit_mb: int = 1024):
        self.memory_limit_mb = memory_limit_mb
        self.process = psutil.Process()
    
    def check_memory(self) -> bool:
        """Check if memory usage is above limit"""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        return memory_mb > self.memory_limit_mb
    
    def force_cleanup(self):
        """Force garbage collection and memory cleanup"""
        gc.collect()
        if hasattr(gc, 'collect'):
            gc.collect(2)  # Force full collection


def process_single_pdf_optimized(pdf_file: Path, db: LmdbDocumentStore, 
                                tesseract_path: str, config: ProcessingConfig,
                                hash_cache: FileHashCache, checkpoint: ProcessingCheckpoint) -> dict:
    """Process a single PDF with optimizations"""
    result = {
        "file_name": pdf_file.name,
        "success": False,
        "pages_processed": 0,
        "error": None,
        "processing_time": 0
    }
    
    start_time = time.time()
    
    try:
        # Check if already processed
        if config.skip_existing and checkpoint.is_completed(pdf_file.name):
            result["success"] = True
            result["pages_processed"] = 0
            result["error"] = "Already processed"
            return result
        
        # Generate document ID from filename
        doc_id = pdf_file.stem
        
        # Check if file has changed
        current_hash = hash_cache.get_hash(str(pdf_file))
        metadata = db.get_document_metadata(doc_id)
        
        if metadata and 'file_hash' in metadata and metadata['file_hash']:
            if metadata['file_hash'] == current_hash:
                result["success"] = True
                result["pages_processed"] = 0
                result["error"] = "File unchanged"
                checkpoint.mark_completed(pdf_file.name)
                return result
        
        # Open PDF document with memory optimization
        with fitz.open(str(pdf_file)) as doc:
            page_count = len(doc)
            
            # Process pages in chunks to manage memory
            digital_texts = []
            ocr_texts = []
            
            if config.enable_digital:
                print(f"  Extracting digital text from {page_count} pages...")
                digital_texts = extract_text_from_pdf_digital(str(pdf_file))
            
            if config.enable_ocr:
                print(f"  Extracting OCR text from images...")
                ocr_texts = extract_text_from_pdf_images_ocr(doc, tesseract_path)
            
            # Prepare batch data for database
            page_data = []
            for page_num in range(page_count):
                digital_text = digital_texts[page_num] if page_num < len(digital_texts) else ""
                ocr_text = ocr_texts[page_num] if page_num < len(ocr_texts) else ""
                page_data.append((digital_text, ocr_text))
            
            # Save document metadata
            metadata = {
                "page_count": page_count,
                "file_size": pdf_file.stat().st_size,
                "processing_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_hash": current_hash,
                "last_modified": pdf_file.stat().st_mtime
            }
            db.save_document_metadata(doc_id, str(pdf_file), pdf_file.name, metadata)
            
            # Save page texts in batch
            db.save_page_texts_batch(doc_id, page_data)
            
            result["success"] = True
            result["pages_processed"] = page_count
            
            # Mark as completed
            checkpoint.mark_completed(pdf_file.name)
            
    except Exception as e:
        result["error"] = str(e)
        checkpoint.mark_failed(pdf_file.name, str(e))
        print(f"  ✗ Error processing {pdf_file.name}: {e}")
    
    finally:
        result["processing_time"] = time.time() - start_time
    
    return result


def process_pdf_folder_optimized(folder_path: str, db_path: str = "document_store.lmdb", 
                                tesseract_path: str = None, config: ProcessingConfig = None):
    """
    Process all PDFs in a folder with comprehensive optimizations.
    
    Args:
        folder_path: Path to folder containing PDFs
        db_path: Path to LMDB database
        tesseract_path: Optional path to Tesseract executable for OCR
        config: Processing configuration object
    """
    if config is None:
        config = ProcessingConfig()
    
    # Initialize components
    db = LmdbDocumentStore(db_path)
    hash_cache = FileHashCache()
    checkpoint = ProcessingCheckpoint()
    memory_monitor = MemoryMonitor(config.memory_limit_mb)
    
    # Get all PDF files in the folder
    pdf_files = list(Path(folder_path).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    print(f"Configuration: {config.max_workers} workers, batch size: {config.batch_size}")
    
    # Filter out already completed files
    if config.skip_existing:
        remaining_files = [f for f in pdf_files if not checkpoint.is_completed(f.name)]
        print(f"Skipping {len(pdf_files) - len(remaining_files)} already processed files")
        pdf_files = remaining_files
    
    if not pdf_files:
        print("All files already processed!")
        return
    
    # Process files in parallel
    results = []
    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(
                process_single_pdf_optimized, 
                pdf_file, 
                db, 
                tesseract_path, 
                config, 
                hash_cache, 
                checkpoint
            ): pdf_file 
            for pdf_file in pdf_files
        }
        
        # Process results as they complete with progress bar
        with tqdm(total=len(pdf_files), desc="Processing PDFs", unit="file") as pbar:
            for future in as_completed(future_to_file):
                pdf_file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update progress bar
                    pbar.set_description(f"Processing: {pdf_file.name}")
                    pbar.update(1)
                    
                    # Check memory usage and cleanup if needed
                    if memory_monitor.check_memory():
                        print(f"  🧹 Memory usage high, forcing cleanup...")
                        memory_monitor.force_cleanup()
                    
                    # Print result summary
                    if result["success"]:
                        if result["pages_processed"] > 0:
                            print(f"  ✓ {pdf_file.name}: {result['pages_processed']} pages in {result['processing_time']:.2f}s")
                        else:
                            print(f"  ⏭️  {pdf_file.name}: {result['error']}")
                    else:
                        print(f"  ✗ {pdf_file.name}: {result['error']}")
                    
                except Exception as e:
                    print(f"  💥 Unexpected error processing {pdf_file.name}: {e}")
                    results.append({
                        "file_name": pdf_file.name,
                        "success": False,
                        "error": f"Unexpected error: {e}"
                    })
                    pbar.update(1)
    
    # Print summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    total_pages = sum(r["pages_processed"] for r in results if r["success"])
    
    print(f"\n{'='*50}")
    print(f"PROCESSING SUMMARY")
    print(f"{'='*50}")
    print(f"Total files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total pages processed: {total_pages}")
    
    if failed > 0:
        print(f"\nFailed files:")
        for result in results:
            if not result["success"]:
                print(f"  - {result['file_name']}: {result['error']}")
    
    # Close database
    db.close()
    print(f"\nDatabase saved to {db_path}")
    
    # Print checkpoint stats
    checkpoint_stats = checkpoint.get_stats()
    print(f"Checkpoint: {checkpoint_stats['completed']} completed, {checkpoint_stats['failed']} failed")


def main():
    parser = argparse.ArgumentParser(description="Process PDFs in a folder with optimizations and store in LMDB")
    parser.add_argument("folder_path", help="Path to folder containing PDFs")
    parser.add_argument("--db", default="document_store.lmdb", help="LMDB database path")
    parser.add_argument("--tesseract", help="Path to Tesseract executable")
    parser.add_argument("--workers", type=int, default=min(cpu_count(), 8), help="Number of worker threads")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    parser.add_argument("--memory-limit", type=int, default=1024, help="Memory limit in MB before cleanup")
    parser.add_argument("--no-ocr", action="store_true", help="Skip OCR processing")
    parser.add_argument("--no-digital", action="store_true", help="Skip digital text extraction")
    parser.add_argument("--no-skip", action="store_true", help="Don't skip already processed files")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.folder_path):
        print(f"Error: Folder {args.folder_path} does not exist")
        return
    
    if not os.path.isdir(args.folder_path):
        print(f"Error: {args.folder_path} is not a directory")
        return
    
    # Create configuration
    config = ProcessingConfig(
        max_workers=args.workers,
        batch_size=args.batch_size,
        memory_limit_mb=args.memory_limit,
        enable_ocr=not args.no_ocr,
        enable_digital=not args.no_digital,
        skip_existing=not args.no_skip
    )
    
    process_pdf_folder_optimized(args.folder_path, args.db, args.tesseract, config)


if __name__ == "__main__":
    # Example usage without command line arguments
    # Uncomment and modify the line below to run directly
    
    config = ProcessingConfig(
        max_workers=4,
        batch_size=10,
        memory_limit_mb=1024,
        enable_ocr=True,
        enable_digital=True,
        skip_existing=True
    )
    
    process_pdf_folder_optimized(
        "SampleData", 
        tesseract_path=r"C:\Users\mmumbaiwala\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
        config=config
    )
    
    # Or run with command line arguments
    # main()
