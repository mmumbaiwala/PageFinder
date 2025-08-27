#!/usr/bin/env python3
"""
Production test script for fuzzy text search functionality.
This script imports the core functionality and provides clean, production-ready output.
"""

from element_search_core import search_static_text_elements, StaticTextElement, MatchResult

def main():
    """Main test function with clean output"""
    print("FUZZY TEXT SEARCH - PRODUCTION TEST")
    print("="*50)
    
    # Test elements
    elements = [
        StaticTextElement(search_text="SuperSpecial_secrett",
                          max_errors=3,
                          max_error_rate=0.2,
                          match_case=False),
        StaticTextElement(search_text="AnotherText",
                          max_errors=3,
                          max_error_rate=0.5,
                          match_case=False),
        StaticTextElement(search_text="book",
                          max_errors=3,
                          max_error_rate=0.5,
                          match_case=False)
    ]

    # Test text
    ocr_text = "Some big noisy OCR output that includes Superspecial_secrett and other boak AnnotherText ..."
    
    print(f"Test text: '{ocr_text}'")
    print(f"Text length: {len(ocr_text)}")
    print(f"Searching for {len(elements)} elements...")
    
    # Run search with debug mode OFF (clean output)
    matches = search_static_text_elements(elements, ocr_text, debug_mode=False)
    
    print("\n" + "="*50)
    print("SEARCH RESULTS")
    print("="*50)
    
    # Display clean results
    for i, match in enumerate(matches):
        status = "✓ SUCCESS" if match.success else "✗ FAILED"
        search_text = elements[i].search_text
        if match.errors >= 0:
            print(f"{status} | '{search_text}' -> Matched: '{match.matched_string}', Errors: {match.errors}, Rate: {match.error_rate:.4f}")
        else:
            print(f"{status} | '{search_text}' -> No match found")
    
    # Summary
    successful = sum(1 for match in matches if match.success)
    total = len(matches)
    print(f"\nSummary: {successful}/{total} searches successful")
    
    if successful == total:
        print("🎉 All searches completed successfully!")
    else:
        print(f"⚠️  {total - successful} searches failed")

if __name__ == "__main__":
    main()
