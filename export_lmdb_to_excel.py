import pandas as pd
from pathlib import Path
from lmdb_document_store import LmdbDocumentStore
import argparse
from datetime import datetime


def export_lmdb_to_excel(db_path: str = "document_store.lmdb", output_file: str = None):
    """
    Export LMDB database contents to Excel file with multiple sheets.
    
    Args:
        db_path: Path to LMDB database
        output_file: Output Excel file path (auto-generated if None)
    """
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"lmdb_export_{timestamp}.xlsx"
    
    try:
        # Open database
        db = LmdbDocumentStore(db_path)
        
        # Get all documents
        docs = db.list_all_docs()
        
        if not docs:
            print("No documents found in database")
            return
        
        print(f"Exporting {len(docs)} documents to {output_file}")
        
        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            # Sheet 1: Document Overview
            print("Creating Document Overview sheet...")
            overview_data = []
            
            for doc_id in docs:
                metadata = db.get_document_metadata(doc_id)
                if metadata:
                    overview_data.append({
                        'Document ID': doc_id,
                        'File Name': metadata.get('file_name', 'N/A'),
                        'File Path': metadata.get('file_path', 'N/A'),
                        'Page Count': metadata.get('page_count', 'N/A'),
                        'File Size (bytes)': metadata.get('file_size', 'N/A'),
                        'File Hash': metadata.get('file_hash', 'N/A')[:16] + '...' if metadata.get('file_hash') else 'N/A',
                        'Processing Date': metadata.get('processing_date', 'N/A'),
                        'Last Modified': metadata.get('last_modified', 'N/A')
                    })
            
            overview_df = pd.DataFrame(overview_data)
            overview_df.to_excel(writer, sheet_name='Document Overview', index=False)
            
            # Sheet 2: Page Details (Digital Text)
            print("Creating Digital Text sheet...")
            digital_data = []
            
            for doc_id in docs:
                metadata = db.get_document_metadata(doc_id)
                if metadata and 'page_count' in metadata:
                    for page_num in range(1, metadata['page_count'] + 1):
                        digital_text = db.get_page_digital_text(doc_id, page_num)
                        if digital_text:
                            digital_data.append({
                                'Document ID': doc_id,
                                'Page Number': page_num,
                                'Digital Text': digital_text[:500] + '...' if len(digital_text) > 500 else digital_text,
                                'Text Length': len(digital_text),
                                'File Name': metadata.get('file_name', 'N/A')
                            })
            
            digital_df = pd.DataFrame(digital_data)
            digital_df.to_excel(writer, sheet_name='Digital Text', index=False)
            
            # Sheet 3: Page Details (OCR Text)
            print("Creating OCR Text sheet...")
            ocr_data = []
            
            for doc_id in docs:
                metadata = db.get_document_metadata(doc_id)
                if metadata and 'page_count' in metadata:
                    for page_num in range(1, metadata['page_count'] + 1):
                        ocr_text = db.get_page_ocr_text(doc_id, page_num)
                        if ocr_text:
                            ocr_data.append({
                                'Document ID': doc_id,
                                'Page Number': page_num,
                                'OCR Text': ocr_text[:500] + '...' if len(ocr_text) > 500 else ocr_text,
                                'Text Length': len(ocr_text),
                                'File Name': metadata.get('file_name', 'N/A')
                            })
            
            ocr_df = pd.DataFrame(ocr_data)
            ocr_df.to_excel(writer, sheet_name='OCR Text', index=False)
            
            # Sheet 4: Combined Page Data
            print("Creating Combined Page Data sheet...")
            combined_data = []
            
            for doc_id in docs:
                metadata = db.get_document_metadata(doc_id)
                if metadata and 'page_count' in metadata:
                    for page_num in range(1, metadata['page_count'] + 1):
                        digital_text = db.get_page_digital_text(doc_id, page_num) or ""
                        ocr_text = db.get_page_ocr_text(doc_id, page_num) or ""
                        
                        combined_data.append({
                            'Document ID': doc_id,
                            'File Name': metadata.get('file_name', 'N/A'),
                            'Page Number': page_num,
                            'Digital Text Length': len(digital_text),
                            'OCR Text Length': len(ocr_text),
                            'Total Text Length': len(digital_text) + len(ocr_text),
                            'Has Digital Text': 'Yes' if digital_text else 'No',
                            'Has OCR Text': 'Yes' if ocr_text else 'No',
                            'Digital Text Preview': digital_text[:200] + '...' if len(digital_text) > 200 else digital_text,
                            'OCR Text Preview': ocr_text[:200] + '...' if len(ocr_text) > 200 else ocr_text
                        })
            
            combined_df = pd.DataFrame(combined_data)
            combined_df.to_excel(writer, sheet_name='Combined Page Data', index=False)
            
            # Sheet 5: Summary Statistics
            print("Creating Summary Statistics sheet...")
            summary_data = []
            
            total_pages = sum(metadata.get('page_count', 0) for doc_id in docs if (metadata := db.get_document_metadata(doc_id)))
            total_digital_text = sum(len(db.get_page_digital_text(doc_id, page_num) or "") 
                                   for doc_id in docs 
                                   for page_num in range(1, (db.get_document_metadata(doc_id) or {}).get('page_count', 0) + 1))
            total_ocr_text = sum(len(db.get_page_ocr_text(doc_id, page_num) or "") 
                                for doc_id in docs 
                                for page_num in range(1, (db.get_document_metadata(doc_id) or {}).get('page_count', 0) + 1))
            
            summary_data.append({
                'Metric': 'Total Documents',
                'Value': len(docs)
            })
            summary_data.append({
                'Metric': 'Total Pages',
                'Value': total_pages
            })
            summary_data.append({
                'Metric': 'Total Digital Text Characters',
                'Value': total_digital_text
            })
            summary_data.append({
                'Metric': 'Total OCR Text Characters',
                'Value': total_ocr_text
            })
            summary_data.append({
                'Metric': 'Total Text Characters',
                'Value': total_digital_text + total_ocr_text
            })
            summary_data.append({
                'Metric': 'Average Pages per Document',
                'Value': round(total_pages / len(docs), 2) if docs else 0
            })
            summary_data.append({
                'Metric': 'Export Date',
                'Value': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary Statistics', index=False)
        
        db.close()
        print(f"✅ Export completed successfully!")
        print(f"📁 File saved as: {output_file}")
        print(f"📊 Sheets created: Document Overview, Digital Text, OCR Text, Combined Page Data, Summary Statistics")
        
    except Exception as e:
        print(f"❌ Error exporting database: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Export LMDB database to Excel")
    parser.add_argument("--db", default="document_store.lmdb", help="LMDB database path")
    parser.add_argument("--output", help="Output Excel file path")
    
    args = parser.parse_args()
    
    export_lmdb_to_excel(args.db, args.output)


if __name__ == "__main__":
    # Example usage without command line arguments
    # Uncomment and modify the line below to run directly
    
    export_lmdb_to_excel()
    
    # Or run with command line arguments
    # main()
