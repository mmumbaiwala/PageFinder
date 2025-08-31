import fitz  # PyMuPDF
import pandas as pd
import pytesseract
from PIL import Image
import io

def extract_text_from_image_ocr(image_path_or_bytes,
                                tesseract_path=None,
                                tesseract_config_mode="--psm 4"
                                ):
    """
    Extract text from an image using Tesseract OCR.
    
    Args:
        image_path_or_bytes: Either a file path (str) or image bytes
        tesseract_path: Optional path to tesseract executable (Windows users may need this)
    
    Returns:
        str: Extracted text from the image
        
    Raises:
        Exception: If OCR fails or Tesseract is not found
    """
    try:
        # Set tesseract path if provided (common on Windows)
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Handle both file paths and image bytes
        if isinstance(image_path_or_bytes, str):
            # File path provided
            image = Image.open(image_path_or_bytes)
        else:
            # Image bytes provided
            image = Image.open(io.BytesIO(image_path_or_bytes))
        
        # Extract text using OCR
        text = pytesseract.image_to_string(image,
                                           config=tesseract_config_mode)
        
        return text.strip()
        
    except Exception as e:
        raise Exception(f"OCR failed: {str(e)}")

def extract_text_from_pdf_images_ocr(pdf_path,
                                     tesseract_path=None):
    """
    Extract text from all images in a PDF using OCR.
    
    Args:
        doc: PyMuPDF document object
        tesseract_path: Optional path to tesseract executable
    
    Returns:
        list: List of extracted text from images, sorted by page order
    """
    doc = fitz.open(pdf_path)
    results = ["" for i in range(len(doc))]  # Initialize with empty strings for all pages
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=False)
        
        if not images:
            continue
            
        page_results = []
        
        for img in images:
            xref = img[0]
            
            try:
                # Create pixmap from image
                pix = fitz.Pixmap(doc, xref)
                
                # Convert to PIL Image for OCR
                img_data = pix.tobytes("png")
                
                # Extract text using OCR
                extracted_text = extract_text_from_image_ocr(img_data, tesseract_path)
                
                if extracted_text:
                    page_results.append({
                        'xref': xref,
                        'text': extracted_text,
                        'size': (pix.width, pix.height)
                    })
                
                pix = None  # Free memory
                
            except Exception as e:
                print(f"Failed to process image {xref} on page {page_num + 1}: {e}")
                continue
        
        if page_results:
            # Extract text from all images on this page and join them
            page_text = ' '.join([item['text'] for item in page_results])
            results[page_num] = page_text
    
    return results

# Alternative function using easyocr (no Tesseract installation needed)
def extract_text_from_image_easyocr(image_path_or_bytes):
    """
    Extract text from an image using EasyOCR (no external dependencies).
    
    Args:
        image_path_or_bytes: Either a file path (str) or image bytes
    
    Returns:
        str: Extracted text from the image
    """
    try:
        import easyocr
        
        # Initialize reader (first time will download models)
        reader = easyocr.Reader(['en'])
        
        # Handle both file paths and image bytes
        if isinstance(image_path_or_bytes, str):
            # File path provided
            result = reader.readtext(image_path_or_bytes)
        else:
            # Image bytes provided - save temporarily
            temp_img = Image.open(io.BytesIO(image_path_or_bytes))
            temp_path = "temp_image.png"
            temp_img.save(temp_path)
            result = reader.readtext(temp_path)
            import os
            os.remove(temp_path)  # Clean up
        
        # Extract text from results
        text = ' '.join([item[1] for item in result])
        return text.strip()
        
    except Exception as e:
        raise Exception(f"EasyOCR failed: {str(e)}")
    

def merge_imageText_with_pdfText(image_text:list[str],
                                  pdf_text:list[str])->list[str]:
    """
    """
    assert len(image_text) == len(pdf_text)
    merged_text = [image_text[i] + pdf_text[i] for i in range(len(image_text))]
    return merged_text


def extract_text_from_pdf_digital(pdf_path:str)->list[str]:
    """
    """
    doc = fitz.open(pdf_path)
    text = []
    for page in doc:
        text.append(page.get_text())
    return text

def digital_pdf_get_text(doc:fitz.Document)->list[str]:
    """
    """
    text = []
    for page in doc:
        text.append(page.get_text())
    return text
    

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
    page_finder_result_template:dict = {
        "Index":{},
        "File_Name": "",
        "File_Path": "",
        "Page_Count": 0,
        "Page_Number_Found": 0,
        **search_conditions,
        # "SearchConditions_Satisfied":{}, #{"A":True, "B":False},
    }
    df = pd.DataFrame(page_finder_result_template)
    return df



if __name__ == "__main__":
    pass
#     image_text = ["This is a test message with some text to search in.", "This is a test message with some text to search in."]
#     pdf_text = ["This is a test message with some text to search in.", "This is a test message with some text to search in."]
#     merged_text = merge_imageText_with_pdfText(image_text, pdf_text)
#     print(merged_text)
    # create_page_finder_result_template({"A":None, "B":None, "C":None})
    tesseract_path = r"C:\Users\mmumbaiwala\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    # Example 1: OCR on a specific image
    image_text = extract_text_from_image_ocr("image_5.png",
                                            tesseract_path=tesseract_path,
                                            tesseract_config_mode="--psm 1")
    
    doc = fitz.open("SampleData/sv600_c_normal.pdf")
    image_text = extract_text_from_pdf_images_ocr(
                                doc=doc,
                                tesseract_path=tesseract_path)

    print(len(image_text))
    print(image_text)