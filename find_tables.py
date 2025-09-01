#!/usr/bin/env python3
"""
Find Tables in PDF Documents
============================

Command-line interface for finding tables of interest in processed PDF documents
using the table detection system.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict
import builtins
from tqdm import tqdm

# Safe print for Windows consoles without UTF-8 code page
def _safe_print(*args, **kwargs):
    text = " ".join(str(a) for a in args)
    try:
        builtins.print(text, **kwargs)
    except UnicodeEncodeError:
        builtins.print(text.encode('ascii', 'ignore').decode('ascii'), **kwargs)

# Override module-level print with safe version
print = _safe_print

# Import our table detection system
from table_detector import TableDetector, TableDefinition, TextElement, MatchStrategy
from lmdb_document_store import LmdbDocumentStore

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n📋 {title}")
    print("-" * 40)

def load_database(db_path: str) -> LmdbDocumentStore:
    """Load the LMDB database"""
    try:
        db = LmdbDocumentStore(db_path)
        print(f"✅ Database loaded: {db_path}")
        return db
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        sys.exit(1)

def load_table_definitions(config_file: str) -> List[TableDefinition]:
    """Load table definitions from configuration file"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        tables = []
        for table_dict in config.get('tables', []):
            # Convert text elements
            text_elements = []
            for elem_dict in table_dict.get('text_elements', []):
                elem = TextElement(**elem_dict)
                text_elements.append(elem)
            
            # Create table definition
            table_def = TableDefinition(
                name=table_dict['name'],
                text_elements=text_elements,
                match_strategy=MatchStrategy(table_dict.get('match_strategy', 'min_count')),
                min_elements=table_dict.get('min_elements', 3),
                min_percentage=table_dict.get('min_percentage', 0.6),
                min_score=table_dict.get('min_score', 0.7),
                description=table_dict.get('description', '')
            )
            tables.append(table_def)
        
        print(f"✅ Loaded {len(tables)} table definitions from {config_file}")
        return tables
        
    except Exception as e:
        print(f"❌ Error loading table definitions: {e}")
        sys.exit(1)

def search_single_document(detector: TableDetector, doc_name: str, verbose: bool = False, min_confidence: float = 0.0):
    """Search a single document for tables"""
    print(f"\n🔍 Searching document: {doc_name}")
    
    if verbose:
        print(f"  📄 Processing document with confidence threshold: {min_confidence}")
    
    results = detector.search_document_for_tables(doc_name, min_confidence)
    
    if not results:
        print("  ❌ No table definitions found or document not accessible")
        return
    
    found_tables = [r for r in results if r.found]
    
    if found_tables:
        print(f"  ✅ Found {len(found_tables)} tables:")
        for result in found_tables:
            print(f"    • {result.table_name} (pages: {result.pages_found}, confidence: {result.confidence_score:.2f})")
            if verbose:
                print(f"      Details: {result.match_details}")
                for elem_result in result.element_results:
                    status = "✅" if elem_result.found else "❌"
                    print(f"        {status} {elem_result.element.search_text}: {elem_result.match_details}")
    else:
        print("  ❌ No tables found")
    
    return results

def search_all_documents(detector: TableDetector, verbose: bool = False, min_confidence: float = 0.0, export_file: str = None):
    """Search all documents for tables"""
    print("\n🔍 Searching all documents for tables...")
    
    # Get all document names
    document_names = detector.db.list_all_docs()
    print(f"📚 Found {len(document_names)} documents to search")
    
    # Search each document with progress bar
    all_results = []
    if verbose:
        # Verbose mode: show progress for each document
        for doc_name in tqdm(document_names, desc="Processing documents", unit="doc"):
            doc_results = detector.search_document_for_tables(doc_name, min_confidence)
            all_results.extend(doc_results)
    else:
        # Silent mode: just show progress bar
        for doc_name in tqdm(document_names, desc="Processing documents", unit="doc", leave=False):
            doc_results = detector.search_document_for_tables(doc_name, min_confidence)
            all_results.extend(doc_results)
    
    if not all_results:
        print("❌ No tables found in any documents")
        return all_results
    
    # Filter results by minimum confidence
    filtered_results = [r for r in all_results if r.confidence_score >= min_confidence]
    
    if not filtered_results:
        print(f"❌ No tables found with confidence >= {min_confidence}")
        return filtered_results
    
    # Generate summary
    summary = detector.get_summary_report(filtered_results)
    
    print(f"\n📊 Search Summary:")
    print(f"  • Documents searched: {summary['total_documents_searched']}")
    print(f"  • Tables found: {summary['total_tables_found']}")
    
    # Show results by document
    print_section("Tables by Document")
    for doc_name, tables in summary['tables_by_document'].items():
        if tables:  # Only show documents with tables
            print(f"  📁 {doc_name}:")
            for table in tables:
                print(f"    • {table['table_name']} (pages: {table['pages']}, confidence: {table['confidence']:.2f})")
    
    # Show results by table type
    print_section("Tables by Type")
    for table_name, table_info in summary['tables_by_type'].items():
        if table_info['found_in_documents']:  # Only show tables that were found
            print(f"  📋 {table_name}: {table_info['total_occurrences']} occurrence(s)")
            for occurrence in table_info['found_in_documents']:
                print(f"    • {occurrence['document']} (pages: {occurrence['pages']}, confidence: {occurrence['confidence']:.2f})")
    
    if export_file:
        export_results(filtered_results, export_file)
    
    return filtered_results

def export_results(results: List, output_file: str):
    """Export results to JSON file"""
    try:
        # Convert results to serializable format
        export_data = []
        for result in results:
            export_data.append({
                'table_name': result.table_name,
                'document_name': result.document_name,
                'file_path': result.file_path,
                'found': result.found,
                'pages_found': result.pages_found,
                'confidence_score': result.confidence_score,
                'match_details': result.match_details
            })
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Results exported to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error exporting results: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Find tables of interest in processed PDF documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search all documents for tables
  python find_tables.py --db document_store.lmdb --config table_definitions.json

  # Search specific document
  python find_tables.py --db document_store.lmdb --config table_definitions.json --document "sample.pdf"

  # Verbose output with export
  python find_tables.py --db document_store.lmdb --config table_definitions.json --verbose --export results.json

  # Filter by minimum confidence (e.g., only show results with 0.5+ confidence)
  python find_tables.py --db document_store.lmdb --config table_definitions.json --min-confidence 0.5
        """
    )
    
    parser.add_argument(
        '--db', 
        required=True,
        help='Path to LMDB database directory'
    )
    
    parser.add_argument(
        '--config', 
        required=True,
        help='Path to table definitions JSON file'
    )
    
    parser.add_argument(
        '--document',
        help='Search specific document only (optional)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output with detailed results'
    )
    
    parser.add_argument(
        '--export',
        help='Export results to JSON file'
    )
    parser.add_argument('--min-confidence', type=float, default=0.0, 
                       help='Minimum confidence score to include in results (0.0 to 1.0, default: 0.0)')
    
    args = parser.parse_args()
    
    # Validate confidence range
    if not 0.0 <= args.min_confidence <= 1.0:
        print("❌ Error: min-confidence must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Print header
    print_header("Table Detection in PDF Documents")
    
    # Load database
    db = load_database(args.db)
    
    # Load table definitions
    tables = load_table_definitions(args.config)
    
    # Create table detector
    detector = TableDetector(db)
    for table in tables:
        detector.add_table_definition(table)
    
    print(f"✅ Table detector initialized with {len(tables)} table definitions")
    
    if args.min_confidence > 0.0:
        print(f"🔍 Filtering results with minimum confidence: {args.min_confidence}")
    
    # Perform search
    if args.document:
        # Search single document
        search_single_document(detector, args.document, args.verbose, args.min_confidence)
        results = detector.search_document_for_tables(args.document, args.min_confidence)
    else:
        # Search all documents
        results = search_all_documents(detector, args.verbose, args.min_confidence, args.export)
    
    # Export results if requested
    if args.export and results:
        export_results(results, args.export)
    
    # Cleanup
    db.close()
    
    print("\n" + "=" * 60)
    print("🎯 Table detection complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
