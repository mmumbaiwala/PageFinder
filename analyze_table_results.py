#!/usr/bin/env python3
"""
Analyze Table Detection Results
===============================

This script analyzes exported table detection results to provide detailed statistics
about table occurrences across documents.
"""

import json
import argparse
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set
import sys

def load_results(json_file: str) -> List[Dict]:
    """Load table detection results from JSON file"""
    try:
        with open(json_file, 'r') as f:
            results = json.load(f)
        print(f"✅ Loaded {len(results)} table detection results from {json_file}")
        return results
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        sys.exit(1)

def analyze_table_occurrences(results: List[Dict]) -> Dict:
    """Analyze table occurrences across documents"""
    analysis = {
        'summary': {},
        'tables_by_document': defaultdict(list),
        'documents_by_table': defaultdict(list),
        'multiple_occurrences': defaultdict(list),
        'confidence_stats': defaultdict(list),
        'file_paths': defaultdict(set)
    }
    
    # First, consolidate results by table and document
    consolidated = defaultdict(lambda: defaultdict(list))
    
    for result in results:
        table_name = result['table_name']
        doc_name = result['document_name']
        pages = result['pages_found']
        confidence = result['confidence_score']
        file_path = result.get('file_path', '')
        
        # Group by document and table
        consolidated[doc_name][table_name].append({
            'pages': pages,
            'confidence': confidence,
            'file_path': file_path
        })
    
    # Now process consolidated results
    for doc_name, tables in consolidated.items():
        for table_name, occurrences in tables.items():
            # Combine all pages and calculate average confidence
            all_pages = []
            all_confidences = []
            file_path = ''
            
            for occ in occurrences:
                all_pages.extend(occ['pages'])
                all_confidences.append(occ['confidence'])
                if not file_path and occ['file_path']:
                    file_path = occ['file_path']
            
            # Remove duplicates and sort pages
            unique_pages = sorted(list(set(all_pages)))
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            # Add to various groupings
            analysis['tables_by_document'][doc_name].append({
                'table': table_name,
                'pages': unique_pages,
                'confidence': avg_confidence,
                'file_path': file_path
            })
            
            analysis['documents_by_table'][table_name].append({
                'document': doc_name,
                'pages': unique_pages,
                'confidence': avg_confidence,
                'file_path': file_path
            })
            
            analysis['confidence_stats'][table_name].append(avg_confidence)
            
            if file_path:
                analysis['file_paths'][table_name].add(file_path)
    
    # Calculate summary statistics
    total_results = len(results)
    unique_documents = len(analysis['tables_by_document'])
    unique_tables = len(analysis['documents_by_table'])
    
    analysis['summary'] = {
        'total_detections': total_results,
        'unique_documents': unique_documents,
        'unique_tables': unique_tables,
        'average_detections_per_document': total_results / unique_documents if unique_documents > 0 else 0,
        'average_detections_per_table': total_results / unique_tables if unique_tables > 0 else 0
    }
    
    # Find multiple occurrences
    for table_name, occurrences in analysis['documents_by_table'].items():
        doc_counts = Counter(occ['document'] for occ in occurrences)
        multiple_docs = {doc: count for doc, count in doc_counts.items() if count > 1}
        if multiple_docs:
            analysis['multiple_occurrences'][table_name] = multiple_docs
    
    return analysis

def print_summary_report(analysis: Dict):
    """Print a comprehensive summary report"""
    summary = analysis['summary']
    
    print("\n" + "=" * 80)
    print("📊 TABLE DETECTION ANALYSIS SUMMARY")
    print("=" * 80)
    
    print(f"\n📈 Overall Statistics:")
    print(f"  • Total table detections: {summary['total_detections']}")
    print(f"  • Unique documents analyzed: {summary['unique_documents']}")
    print(f"  • Unique table types found: {summary['unique_tables']}")
    print(f"  • Average detections per document: {summary['average_detections_per_document']:.2f}")
    print(f"  • Average detections per table type: {summary['average_detections_per_table']:.2f}")
    
    # Table-by-table analysis
    print(f"\n📋 Table-by-Table Analysis:")
    print("-" * 60)
    
    for table_name, occurrences in analysis['documents_by_table'].items():
        doc_count = len(set(occ['document'] for occ in occurrences))
        total_occurrences = len(occurrences)
        avg_confidence = sum(occ['confidence'] for occ in occurrences) / len(occurrences)
        confidences = [occ['confidence'] for occ in occurrences]
        min_conf = min(confidences)
        max_conf = max(confidences)
        
        print(f"\n🔍 {table_name}:")
        print(f"  • Found in {doc_count} document(s)")
        print(f"  • Total occurrences: {total_occurrences}")
        print(f"  • Confidence range: {min_conf:.2f} - {max_conf:.2f} (avg: {avg_confidence:.2f})")
        
        # Check for multiple occurrences
        if table_name in analysis['multiple_occurrences']:
            multiple_docs = analysis['multiple_occurrences'][table_name]
            print(f"  • Multiple occurrences in: {len(multiple_docs)} document(s)")
            for doc, count in multiple_docs.items():
                print(f"    - {doc}: {count} occurrence(s)")
    
    # Document-by-document analysis
    print(f"\n📁 Document-by-Document Analysis:")
    print("-" * 60)
    
    for doc_name, tables in analysis['tables_by_document'].items():
        table_count = len(set(table['table'] for table in tables))
        total_occurrences = len(tables)
        avg_confidence = sum(table['confidence'] for table in tables) / len(tables)
        
        print(f"\n📄 {doc_name}:")
        print(f"  • Contains {table_count} different table type(s)")
        print(f"  • Total table occurrences: {total_occurrences}")
        print(f"  • Average confidence: {avg_confidence:.2f}")
        
        # List tables found
        table_summary = defaultdict(list)
        for table in tables:
            table_summary[table['table']].extend(table['pages'])
        
        for table_name, pages in table_summary.items():
            print(f"    - {table_name}: pages {sorted(pages)}")
    
    # Multiple occurrences summary
    if analysis['multiple_occurrences']:
        print(f"\n🔄 Multiple Occurrences Summary:")
        print("-" * 60)
        
        for table_name, doc_counts in analysis['multiple_occurrences'].items():
            total_multiple = sum(doc_counts.values())
            print(f"\n📊 {table_name}:")
            print(f"  • Total multiple occurrences: {total_multiple}")
            for doc, count in doc_counts.items():
                print(f"    - {doc}: {count} occurrence(s)")
    
    # Confidence analysis
    print(f"\n📊 Confidence Analysis:")
    print("-" * 60)
    
    for table_name, confidences in analysis['confidence_stats'].items():
        avg_conf = sum(confidences) / len(confidences)
        high_conf = sum(1 for c in confidences if c >= 0.7)
        medium_conf = sum(1 for c in confidences if 0.4 <= c < 0.7)
        low_conf = sum(1 for c in confidences if c < 0.4)
        
        print(f"\n📈 {table_name}:")
        print(f"  • Average confidence: {avg_conf:.2f}")
        print(f"  • High confidence (≥0.7): {high_conf} occurrence(s)")
        print(f"  • Medium confidence (0.4-0.7): {medium_conf} occurrence(s)")
        print(f"  • Low confidence (<0.4): {low_conf} occurrence(s)")

def export_analysis(analysis: Dict, output_file: str):
    """Export analysis results to JSON file"""
    try:
        # Convert defaultdict to regular dict for JSON serialization
        export_data = {
            'summary': analysis['summary'],
            'tables_by_document': dict(analysis['tables_by_document']),
            'documents_by_table': dict(analysis['documents_by_table']),
            'multiple_occurrences': dict(analysis['multiple_occurrences']),
            'confidence_stats': dict(analysis['confidence_stats']),
            'file_paths': {k: list(v) for k, v in analysis['file_paths'].items()}
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n✅ Analysis exported to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error exporting analysis: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Analyze table detection results from exported JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze results and print summary
  python analyze_table_results.py results.json

  # Export analysis to JSON file
  python analyze_table_results.py results.json --export analysis.json

  # Analyze with custom confidence threshold
  python analyze_table_results.py results.json --min-confidence 0.5
        """
    )
    
    parser.add_argument('input_file', help='Path to exported table detection results JSON file')
    parser.add_argument('--export', help='Export analysis to JSON file')
    parser.add_argument('--min-confidence', type=float, default=0.0,
                       help='Filter results by minimum confidence (0.0 to 1.0)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_file).exists():
        print(f"❌ Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    
    # Load and filter results
    results = load_results(args.input_file)
    
    if args.min_confidence > 0.0:
        original_count = len(results)
        results = [r for r in results if r['confidence_score'] >= args.min_confidence]
        print(f"🔍 Filtered to {len(results)} results with confidence ≥ {args.min_confidence} (from {original_count})")
    
    if not results:
        print("❌ No results to analyze after filtering")
        sys.exit(1)
    
    # Analyze results
    analysis = analyze_table_occurrences(results)
    
    # Print summary
    print_summary_report(analysis)
    
    # Export if requested
    if args.export:
        export_analysis(analysis, args.export)

if __name__ == "__main__":
    main()
