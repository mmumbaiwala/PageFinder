from element_search_core import StaticTextElement, search_static_text_elements

def test_error_rate_calculation():
    """Test the corrected error rate calculation and filtering."""
    
    print("Testing Error Rate Calculation and Filtering")
    print("=" * 50)
    
    # Test case 1: Short pattern with high error tolerance
    print("\n1. Testing 'COM' with max_errors=1, max_error_rate=0.3")
    elements = [
        StaticTextElement(
            search_text="COM",
            max_errors=1,
            max_error_rate=0.3,
            match_case=False
        )
    ]
    
    # Test with "CQM" (1 error in 3 characters = 33.3% error rate)
    test_text = "This is a CQM message"
    results = search_static_text_elements(elements, test_text, debug_mode=True)
    
    for i, result in enumerate(results):
        print(f"\nResult: {result}")
        print(f"  Pattern: '{elements[i].search_text}'")
        print(f"  Matched: '{result.matched_string}'")
        print(f"  Errors: {result.errors}")
        print(f"  Error Rate: {result.error_rate:.4f} ({result.error_rate*100:.1f}%)")
        print(f"  Success: {result.success}")
    
    # Test case 2: Longer pattern with percentage-based tolerance
    print("\n" + "="*50)
    print("2. Testing 'Relationship Name' with max_errors=2")
    elements = [
        StaticTextElement(
            search_text="Relationship Name",
            max_errors=2,
            match_case=True
        )
    ]
    
    # Test with "Relationship Nme" (1 error in 18 characters = 5.6% error rate)
    test_text = "This is a Relationship Nme field"
    results = search_static_text_elements(elements, test_text, debug_mode=True)
    
    for i, result in enumerate(results):
        print(f"\nResult: {result}")
        print(f"  Pattern: '{elements[i].search_text}'")
        print(f"  Matched: '{result.matched_string}'")
        print(f"  Errors: {result.errors}")
        print(f"  Error Rate: {result.error_rate:.4f} ({result.error_rate*100:.1f}%)")
        print(f"  Success: {result.success}")
    
    # Test case 3: Edge case - exact match
    print("\n" + "="*50)
    print("3. Testing exact match case")
    elements = [
        StaticTextElement(
            search_text="exact",
            max_errors=0,
            max_error_rate=0.0,
            match_case=False
        )
    ]
    
    test_text = "This is an exact match"
    results = search_static_text_elements(elements, test_text, debug_mode=True)
    
    for i, result in enumerate(results):
        print(f"\nResult: {result}")
        print(f"  Pattern: '{elements[i].search_text}'")
        print(f"  Matched: '{result.matched_string}'")
        print(f"  Errors: {result.errors}")
        print(f"  Error Rate: {result.error_rate:.4f} ({result.error_rate*100:.1f}%)")
        print(f"  Success: {result.success}")

if __name__ == "__main__":
    test_error_rate_calculation()
