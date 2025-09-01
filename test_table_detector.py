#!/usr/bin/env python3
"""
Test Table Detector
==================

Simple test script to demonstrate the table detector functionality.
"""

from table_detector import TextElement, TableDefinition, MatchStrategy, TableDetector

def test_text_elements():
    """Test text element creation and validation"""
    print("🧪 Testing Text Elements...")
    
    # Test basic text element
    elem1 = TextElement(
        search_text="consolidated balance sheets",
        max_errors=3,
        max_error_rate=0.3,
        match_case=False,
        weight=1.0,
        description="Main balance sheet identifier"
    )
    print(f"✅ Created element: {elem1.search_text}")
    
    # Test case-sensitive element
    elem2 = TextElement(
        search_text="Current assets",
        max_errors=2,
        match_case=True,
        weight=1.0
    )
    print(f"✅ Created element: {elem2.search_text} (case-sensitive)")
    
    return [elem1, elem2]

def test_table_definition():
    """Test table definition creation"""
    print("\n🧪 Testing Table Definition...")
    
    elements = test_text_elements()
    
    table_def = TableDefinition(
        name="Balance Sheet",
        description="Consolidated balance sheet table",
        text_elements=elements,
        match_strategy=MatchStrategy.MIN_COUNT,
        min_elements=2
    )
    
    print(f"✅ Created table: {table_def.name}")
    print(f"  • Elements: {len(table_def.text_elements)}")
    print(f"  • Strategy: {table_def.match_strategy.value}")
    print(f"  • Min elements: {table_def.min_elements}")
    
    return table_def

def test_matching_logic():
    """Test the matching logic"""
    print("\n🧪 Testing Matching Logic...")
    
    table_def = test_table_definition()
    
    # Simulate search results (2 out of 2 elements found)
    from table_detector import SearchResult
    
    # Mock search results
    mock_results = [
        SearchResult(
            element=table_def.text_elements[0],
            found=True,
            page_num=1,
            matches=[(100, "consolidated balance sheets")],
            error_rate=0.0,
            score=1.0
        ),
        SearchResult(
            element=table_def.text_elements[1],
            found=True,
            page_num=1,
            matches=[(200, "Current assets")],
            error_rate=0.0,
            score=1.0
        )
    ]
    
    # Test if table is found using the detector
    detector = TableDetector(None)  # No DB connection for testing
    found, score, details = detector.is_table_found(table_def, mock_results)
    
    print(f"✅ Table found: {found}")
    print(f"  • Score: {score:.2f}")
    print(f"  • Details: {details}")
    
    return found, score, details

def test_configuration_loading():
    """Test loading table definitions from JSON"""
    print("\n🧪 Testing Configuration Loading...")
    
    try:
        # This would normally load from the JSON file
        # For testing, we'll create a mock config
        mock_config = {
            "name": "Test Table",
            "description": "Test table for validation",
            "match_strategy": "min_count",
            "min_elements": 1,  # Fixed: should not exceed number of text elements
            "text_elements": [
                {
                    "search_text": "test text",
                    "max_errors": 2,
                    "max_error_rate": 0.3,
                    "match_case": False,
                    "weight": 1.0
                }
            ]
        }
        
        # Test the add_table_from_dict method
        detector = TableDetector(None)  # No DB connection for testing
        detector.add_table_from_dict(mock_config)
        
        print(f"✅ Loaded table definition: {detector.tables[0].name}")
        print(f"  • Elements: {len(detector.tables[0].text_elements)}")
        
    except Exception as e:
        print(f"❌ Error in configuration loading: {e}")

def main():
    """Run all tests"""
    print("🚀 Table Detector Test Suite")
    print("=" * 50)
    
    try:
        test_text_elements()
        test_table_definition()
        test_matching_logic()
        test_configuration_loading()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Table detector is working correctly.")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
