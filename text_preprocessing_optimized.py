import fitz  # PyMuPDF
import pandas as pd
import pytesseract
from PIL import Image
import io
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from typing import List, Optional, Tuple
import time


def extract_text_from_image_ocr_optimized(image_data: bytes,
                                        tesseract_path: str = None,
                                        tesseract_config_mode: str = "--psm 4",
                                        timeout: int = 30) -> str:
    """
    Extract text from an image using Tesseract OCR with timeout and error handling.
    
    Args:
        image_data: Image bytes
        tesseract_path: Optional path to tesseract executable
        tesseract_config_mode: Tesseract configuration mode
        timeout: Timeout in seconds for OCR processing
    
    Returns:
        str: Extracted text from the image
        
    Raises:
        Exception: If OCR fails or Tesseract is not found
    """
    try:
        # Set tesseract path if provided (common on Windows)
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Extract text using OCR with timeout
        text = pytesseract.image_to_string(
            image,
            config=tesseract_config_mode,
            timeout=timeout
        )
        
        return text.strip()
        
    except Exception as e:
        raise Exception(f"OCR failed: {str(e)}")


def extract_text_from_pdf_images_ocr_optimized(doc: fitz.Document,
                                              tesseract_path: str = None,
                                              max_workers: int = None,
                                              batch_size: int = 5,
                                              memory_limit_mb: int = 512) -> List[str]:
    """
    Extract text from all images in a PDF using optimized OCR with batching and parallel processing.
    
    Args:
        doc: PyMuPDF document object
        tesseract_path: Optional path to tesseract executable
        max_workers: Maximum number of worker threads for OCR
        batch_size: Number of images to process in each batch
        memory_limit_mb: Memory limit in MB before forcing cleanup
    
    Returns:
        list: List of extracted text from images, sorted by page order
    """
    if max_workers is None:
        max_workers = min(cpu_count(), 4)  # Limit OCR workers to avoid overwhelming system
    
    results = ["" for _ in range(len(doc))]
    
    # Collect all images with their page numbers
    all_images = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=False)
        
        for img in images:
            xref = img[0]
            all_images.append((page_num, xref, img))
    
    if not all_images:
        return results
    
    print(f"  Found {len(all_images)} images across {len(doc)} pages")
    
    # Process images in batches to manage memory
    for batch_start in range(0, len(all_images), batch_size):
        batch_end = min(batch_start + batch_size, len(all_images))
        batch = all_images[batch_start:batch_end]
        
        print(f"  Processing batch {batch_start//batch_size + 1}/{(len(all_images) + batch_size - 1)//batch_size}")
        
        # Process batch with parallel OCR
        batch_results = _process_image_batch_parallel(
            doc, batch, tesseract_path, max_workers
        )
        
        # Update results
        for page_num, text in batch_results:
            if results[page_num]:  # Append to existing text
                results[page_num] += " " + text
            else:
                results[page_num] = text
        
        # Memory cleanup between batches
        if batch_start % (batch_size * 2) == 0:
            gc.collect()
    
    return results


def _process_image_batch_parallel(doc: fitz.Document,
                                 image_batch: List[Tuple[int, int, tuple]],
                                 tesseract_path: str,
                                 max_workers: int) -> List[Tuple[int, str]]:
    """
    Process a batch of images in parallel using ThreadPoolExecutor.
    
    Args:
        doc: PyMuPDF document object
        image_batch: List of (page_num, xref, img_info) tuples
        tesseract_path: Path to tesseract executable
        max_workers: Maximum number of worker threads
    
    Returns:
        List of (page_num, extracted_text) tuples
    """
    results = []
    
    def process_single_image(args):
        page_num, xref, img_info = args
        try:
            # Create pixmap from image
            pix = fitz.Pixmap(doc, xref)
            
            # Convert to bytes for OCR
            img_data = pix.tobytes("png")
            
            # Extract text using OCR
            extracted_text = extract_text_from_image_ocr_optimized(
                img_data, tesseract_path
            )
            
            # Clean up pixmap
            pix = None
            
            return page_num, extracted_text if extracted_text else ""
            
        except Exception as e:
            print(f"    Failed to process image {xref} on page {page_num + 1}: {e}")
            return page_num, ""
    
    # Process images in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_image = {
            executor.submit(process_single_image, img_data): img_data 
            for img_data in image_batch
        }
        
        for future in as_completed(future_to_image):
            try:
                page_num, text = future.result()
                if text:  # Only add non-empty results
                    results.append((page_num, text))
            except Exception as e:
                print(f"    Error in parallel OCR processing: {e}")
    
    return results


def extract_text_from_pdf_digital_optimized(pdf_path: str, chunk_size: int = 10) -> List[str]:
    """
    Extract digital text from PDF with memory optimization.
    
    Args:
        pdf_path: Path to PDF file
        chunk_size: Number of pages to process in each chunk
    
    Returns:
        List of extracted text from each page
    """
    results = []
    
    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)
        
        # Process pages in chunks to manage memory
        for start_page in range(0, total_pages, chunk_size):
            end_page = min(start_page + chunk_size, total_pages)
            
            chunk_results = []
            for page_num in range(start_page, end_page):
                try:
                    page = doc[page_num]
                    text = page.get_text()
                    chunk_results.append(text.strip())
                except Exception as e:
                    print(f"    Error extracting text from page {page_num + 1}: {e}")
                    chunk_results.append("")
            
            results.extend(chunk_results)
            
            # Memory cleanup between chunks
            if start_page % (chunk_size * 2) == 0:
                gc.collect()
    
    return results


def digital_pdf_get_text_optimized(doc: fitz.Document, chunk_size: int = 10) -> List[str]:
    """
    Extract digital text from PyMuPDF document with memory optimization.
    
    Args:
        doc: PyMuPDF document object
        chunk_size: Number of pages to process in each chunk
    
    Returns:
        List of extracted text from each page
    """
    results = []
    total_pages = len(doc)
    
    # Process pages in chunks to manage memory
    for start_page in range(0, total_pages, chunk_size):
        end_page = min(start_page + chunk_size, total_pages)
        
        chunk_results = []
        for page_num in range(start_page, end_page):
            try:
                page = doc[page_num]
                text = page.get_text()
                chunk_results.append(text.strip())
            except Exception as e:
                print(f"    Error extracting text from page {page_num + 1}: {e}")
                chunk_results.append("")
        
        results.extend(chunk_results)
        
        # Memory cleanup between chunks
        if start_page % (chunk_size * 2) == 0:
            gc.collect()
    
    return results


def merge_imageText_with_pdfText_optimized(image_text: List[str],
                                          pdf_text: List[str]) -> List[str]:
    """
    Merge image OCR text with PDF digital text efficiently.
    
    Args:
        image_text: List of OCR text from images
        pdf_text: List of digital text from PDF
    
    Returns:
        List of merged text for each page
    """
    assert len(image_text) == len(pdf_text), "Text lists must have same length"
    
    # Use list comprehension for better performance
    merged_text = []
    for i in range(len(image_text)):
        combined = f"{image_text[i]} {pdf_text[i]}".strip()
        merged_text.append(combined)
    
    return merged_text


def create_page_finder_result_template(search_conditions):
    """
    Create a template DataFrame for storing page finding results.
    
    This function generates a standardized template structure for tracking
    the results of page finding operations across PDF documents. The template
    includes fields for document metadata, page information, and search condition
    results.
    
    Returns:
        pandas.DataFrame: A DataFrame with the following columns:
            - Index: Dictionary field for storing page indices
            - File_Name: String field for the name of the processed file
            - File_Path: String field for the full path to the file
            - Page_Count: Integer field for total number of pages in the document
            - Page_Number_Found: Integer field for the page number where search
              conditions were satisfied
            - SearchConditions_Satisfied: Dictionary field for storing boolean
              results of each search condition (e.g., {"A": True, "B": False})
    
    Example:
        >>> template_df = create_page_finder_result_template()
        >>> print(template_df.columns.tolist())
        ['Index', 'File_Name', 'File_Path', 'Page_Count', 'Page_Number_Found', 'SearchConditions_Satisfied']
    
    Note:
        - The DataFrame is initialized with empty/default values
        - SearchConditions_Satisfied field is designed to store results from
          search_conditions_document function
        - This template serves as a foundation for building result datasets
          from multiple document searches
    """
    page_finder_result_template: dict = {
        "Index": {},
        "File_Name": "",
        "File_Path": "",
        "Page_Count": 0,
        "Page_Number_Found": 0,
        **search_conditions,
        # "SearchConditions_Satisfied":{}, #{"A":True, "B":False},
    }
    df = pd.DataFrame(page_finder_result_template)
    return df


# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor and log performance metrics for text extraction operations"""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start_operation(self, operation_name: str):
        """Start timing an operation"""
        self.start_time = time.time()
        self.metrics[operation_name] = {"start": self.start_time}
    
    def end_operation(self, operation_name: str, additional_info: dict = None):
        """End timing an operation and record metrics"""
        if self.start_time and operation_name in self.metrics:
            end_time = time.time()
            duration = end_time - self.start_time
            self.metrics[operation_name].update({
                "end": end_time,
                "duration": duration,
                "additional_info": additional_info or {}
            })
    
    def get_summary(self) -> dict:
        """Get performance summary"""
        summary = {}
        for op_name, metrics in self.metrics.items():
            if "duration" in metrics:
                summary[op_name] = {
                    "duration_seconds": metrics["duration"],
                    "additional_info": metrics.get("additional_info", {})
                }
        return summary


if __name__ == "__main__":
    # Example usage and testing
    tesseract_path = r"C:\Users\mmumbaiwala\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    
    # Test optimized OCR
    doc = fitz.open("SampleData/sv600_c_normal.pdf")
    image_text = extract_text_from_pdf_images_ocr_optimized(
        doc=doc,
        tesseract_path=tesseract_path,
        max_workers=2,
        batch_size=3
    )
    
    print(f"Extracted text from {len(image_text)} pages")
    print(f"Sample text from first page: {image_text[0][:100]}...")
    
    # Test optimized digital text extraction
    digital_text = digital_pdf_get_text_optimized(doc, chunk_size=5)
    print(f"Digital text from {len(digital_text)} pages")
    
    # Test merging
    merged = merge_imageText_with_pdfText_optimized(image_text, digital_text)
    print(f"Merged text from {len(merged)} pages")
    
    # Performance monitoring example
    monitor = PerformanceMonitor()
    monitor.start_operation("test_ocr")
    time.sleep(1)  # Simulate processing
    monitor.end_operation("test_ocr", {"pages_processed": len(image_text)})
    
    print("Performance summary:", monitor.get_summary())
