#!/usr/bin/env python3
"""
Table Detector Demo
==================

This script demonstrates how to use the table detection system
to find tables of interest in PDF documents.
"""

from table_detector import TextElement, TableDefinition, MatchStrategy, TableDetector

def create_sample_table_definitions():
    """Create sample table definitions for demonstration"""
    print("🔧 Creating sample table definitions...")
    
    # Balance Sheet table
    balance_sheet_elements = [
        TextElement(
            search_text="consolidated balance sheets",
            max_errors=3,
            max_error_rate=0.3,
            match_case=False,
            weight=1.0,
            description="Main balance sheet identifier"
        ),
        TextElement(
            search_text="Current assets",
            max_errors=2,
            match_case=True,
            weight=1.0,
            description="Current assets section"
        ),
        TextElement(
            search_text="Total assets",
            max_errors=2,
            match_case=True,
            weight=1.0,
            description="Total assets line"
        )
    ]
    
    balance_sheet = TableDefinition(
        name="Balance Sheet",
        description="Consolidated balance sheet table",
        text_elements=balance_sheet_elements,
        match_strategy=MatchStrategy.MIN_COUNT,
        min_elements=2  # Need at least 2 out of 3 elements
    )
    
    print(f"✅ Created '{balance_sheet.name}' table definition")
    print(f"  • Elements: {len(balance_sheet.text_elements)}")
    print(f"  • Strategy: {balance_sheet.match_strategy.value}")
    print(f"  • Min elements required: {balance_sheet.min_elements}")
    
    return [balance_sheet]

def demonstrate_search_logic():
    """Demonstrate the search and matching logic"""
    print("\n🔍 Demonstrating search logic...")
    
    tables = create_sample_table_definitions()
    balance_sheet = tables[0]
    
    # Simulate searching through a document
    print(f"\n📄 Simulating search through document pages...")
    
    # Page 1: Contains balance sheet elements
    page1_text = """
    CONSOLIDATED BALANCE SHEETS
    (in millions)
    
    Current assets:
    Cash and cash equivalents     $1,234
    Total current assets         $5,678
    
    Total assets                 $12,345
    """
    
    # Page 2: Contains some balance sheet elements
    page2_text = """
    Current assets:
    Accounts receivable          $2,345
    
    Total assets                 $12,345
    """
    
    # Page 3: No balance sheet elements
    page3_text = """
    Notes to financial statements
    Note 1: Summary of significant accounting policies
    """
    
    # Create detector (no DB connection needed for demo)
    detector = TableDetector(None)
    detector.add_table_definition(balance_sheet)
    
    # Search each page
    pages = [page1_text, page2_text, page3_text]
    
    for page_num, page_text in enumerate(pages, 1):
        print(f"\n📖 Page {page_num}:")
        
        # Search for each text element
        element_results = []
        for element in balance_sheet.text_elements:
            result = detector.search_text_element(element, page_text, page_num)
            element_results.append(result)
            
            status = "✅" if result.found else "❌"
            print(f"  {status} {element.search_text}: {'Found' if result.found else 'Not found'}")
        
        # Check if table is found on this page
        found, score, details = detector.is_table_found(balance_sheet, element_results)
        
        print(f"  📊 Table '{balance_sheet.name}': {'✅ FOUND' if found else '❌ NOT FOUND'}")
        print(f"     Score: {score:.2f}, Details: {details}")

def demonstrate_different_strategies():
    """Demonstrate different matching strategies"""
    print("\n🎯 Demonstrating different matching strategies...")
    
    # Create a simple table with 4 elements
    elements = [
        TextElement(search_text="Element 1", weight=1.0),
        TextElement(search_text="Element 2", weight=1.0),
        TextElement(search_text="Element 3", weight=1.0),
        TextElement(search_text="Element 4", weight=1.0)
    ]
    
    # Test different strategies
    strategies = [
        ("ALL_ELEMENTS", MatchStrategy.ALL_ELEMENTS, 4, 0.6, 0.7),
        ("MIN_COUNT", MatchStrategy.MIN_COUNT, 3, 0.6, 0.7),
        ("MIN_PERCENTAGE", MatchStrategy.MIN_PERCENTAGE, 3, 0.75, 0.7),
        ("WEIGHTED_SCORE", MatchStrategy.WEIGHTED_SCORE, 3, 0.6, 0.8)
    ]
    
    detector = TableDetector(None)
    
    for strategy_name, strategy, min_elements, min_percentage, min_score in strategies:
        print(f"\n📋 Strategy: {strategy_name}")
        
        table_def = TableDefinition(
            name=f"Test Table ({strategy_name})",
            text_elements=elements,
            match_strategy=strategy,
            min_elements=min_elements,
            min_percentage=min_percentage,
            min_score=min_score
        )
        
        # Simulate finding 3 out of 4 elements
        mock_results = []
        for i, element in enumerate(elements):
            found = i < 3  # First 3 elements found
            mock_results.append(
                detector.search_text_element(element, "dummy text", 1)
            )
            # Override the found status
            mock_results[-1].found = found
        
        found, score, details = detector.is_table_found(table_def, mock_results)
        
        print(f"  • Elements found: 3/4")
        print(f"  • Table found: {'✅ YES' if found else '❌ NO'}")
        print(f"  • Score: {score:.2f}")
        print(f"  • Details: {details}")

def main():
    """Main demonstration function"""
    print("🚀 Table Detector Demonstration")
    print("=" * 60)
    
    try:
        # Show how to create table definitions
        create_sample_table_definitions()
        
        # Demonstrate search logic
        demonstrate_search_logic()
        
        # Show different matching strategies
        demonstrate_different_strategies()
        
        print("\n" + "=" * 60)
        print("🎉 Demonstration complete!")
        print("\n💡 Key Features:")
        print("  • Configurable text elements with fuzzy matching")
        print("  • Multiple matching strategies (all, min_count, percentage, weighted)")
        print("  • Error tolerance and confidence scoring")
        print("  • Easy JSON configuration")
        print("  • Fast search through processed PDF text")
        
        print("\n🚀 Next steps:")
        print("  • Use with your LMDB database: python find_tables.py --db document_store.lmdb --config table_definitions.json")
        print("  • Customize table definitions in table_definitions.json")
        print("  • Add your own text elements and matching strategies")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
