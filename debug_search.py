#!/usr/bin/env python3
"""
Debug script for testing the fuzzy text search function.
This script will help identify why Levenshtein distance calculations 
are not working as expected.
"""

from rapidfuzz import fuzz, distance
from attrs import define, field, validators
from typing import Optional, Tuple

@define
class StaticTextElement:
    search_text: str = field(validator=validators.instance_of(str))
    max_errors: int = field(validator=validators.instance_of(int))
    max_error_rate: float = field(validator=validators.instance_of(float))
    match_case: bool = field(validator=validators.instance_of(bool))

@define
class MatchResult:
    search_text: str = field(validator=validators.instance_of(str))
    errors: int = field(validator=validators.instance_of(int))
    error_rate: float = field(validator=validators.instance_of(float))
    match_case: bool = field(validator=validators.instance_of(bool))
    success: bool = field(validator=validators.instance_of(bool))

def search_static_text_elements(elements: list[StaticTextElement],
                                text: str,
                                max_hypothesis: int = 3,
                                max_window_size: int = 11,
                                debug_mode: bool = False) -> list[MatchResult]:
    """
    Search for static text elements with fuzzy matching.
    
    Args:
        elements: List of StaticTextElement to search for
        text: Text to search within
        max_hypothesis: Maximum number of best matches to keep for each element
        max_window_size: Additional characters to add to pattern length for window size
        debug_mode: If True, print detailed search process. If False, print clean output.
    
    Returns:
        List of MatchResult objects (one per element, with best match)
    """
    results = []

    for element in elements:
        if element.match_case:
            text_to_search = text
            pattern = element.search_text
        else:
            text_to_search = text.lower()
            pattern = element.search_text.lower()

        pattern_len = len(pattern)
        window_size = pattern_len + max_window_size  # allow some flexibility
        
        # Keep track of top N hypotheses for this element
        hypotheses = []  # List of (score, errors, substring) tuples
        
        if debug_mode:
            print(f"\n=== Searching for '{element.search_text}' ===")
            print(f"Pattern (normalized): '{pattern}' (length: {pattern_len})")
            print(f"Window size: {window_size}")
            print(f"Max hypotheses to keep: {max_hypothesis}")

        # Quick exact match shortcut
        if pattern in text_to_search:
            if debug_mode:
                print(f"✓ Exact match found!")
            results.append(MatchResult(
                search_text=element.search_text,
                errors=0,
                error_rate=0.0,
                match_case=element.match_case,
                success=True
            ))
            continue

        # Sliding window fuzzy search
        for i in range(len(text_to_search) - window_size + 1):
            snippet = text_to_search[i:i+window_size]
            
            # Use partial_ratio for scoring
            score = fuzz.partial_ratio(pattern, snippet)
            
            # Find the best substring within the snippet - try different lengths
            best_substring_in_snippet = None
            best_substring_score = -1
            
            # Try different substring lengths around the pattern length
            # This allows us to find complete words that might be longer/shorter than pattern
            for length_offset in range(-2, 4):  # Try lengths: pattern_len-2, pattern_len-1, pattern_len, pattern_len+1, pattern_len+2
                target_length = pattern_len + length_offset
                if target_length <= 0 or target_length > len(snippet):
                    continue
                    
                for j in range(len(snippet) - target_length + 1):
                    sub_snippet = snippet[j:j + target_length]
                    sub_score = fuzz.ratio(pattern, sub_snippet)
                    
                    if sub_score > best_substring_score:
                        best_substring_score = sub_score
                        best_substring_in_snippet = sub_snippet
            
            # Calculate Levenshtein distance for the best substring
            if best_substring_in_snippet:
                errors = distance.Levenshtein.distance(pattern, best_substring_in_snippet)
                
                # Create hypothesis tuple: (score, errors, substring, position)
                hypothesis = (score, errors, best_substring_in_snippet, i)
                
                # Check if this hypothesis is worth keeping
                should_add = False
                
                if len(hypotheses) < max_hypothesis:
                    # Always add if we haven't reached max_hypothesis
                    should_add = True
                else:
                    # Check if this hypothesis is better than any existing ones
                    worst_hypothesis = max(hypotheses, key=lambda x: (x[1], -x[0]))  # Worst by errors, then by score
                    if errors < worst_hypothesis[1] or (errors == worst_hypothesis[1] and score > worst_hypothesis[0]):
                        should_add = True
                
                if should_add:
                    # Add new hypothesis
                    hypotheses.append(hypothesis)
                    
                    # Keep only top max_hypothesis hypotheses
                    if len(hypotheses) > max_hypothesis:
                        # Sort by errors (ascending), then by score (descending)
                        hypotheses.sort(key=lambda x: (x[1], -x[0]))
                        hypotheses = hypotheses[:max_hypothesis]
                    
                    if debug_mode:
                        print(f"  New hypothesis added: score={score:.1f}, errors={errors}, substring='{best_substring_in_snippet}', pos={i}")
                        print(f"  Current top {len(hypotheses)} hypotheses:")
                        for idx, (s, e, sub, pos) in enumerate(hypotheses):
                            print(f"    {idx+1}. Score: {s:.1f}, Errors: {e}, Substring: '{sub}', Position: {pos}")

        # Select the best hypothesis (lowest errors, then highest score)
        if hypotheses:
            # Sort by errors (ascending), then by score (descending)
            hypotheses.sort(key=lambda x: (x[1], -x[0]))
            best_score, best_errors, best_substring, best_position = hypotheses[0]
            
            if debug_mode:
                print(f"\n  Best hypothesis selected:")
                print(f"    Score: {best_score:.1f}, Errors: {best_errors}, Substring: '{best_substring}', Position: {best_position}")
            
            # Calculate error rate based on actual substring length
            actual_length = len(best_substring) if best_substring else pattern_len
            error_rate = best_errors / max(1, actual_length)
            
            success = (
                best_errors <= element.max_errors and
                error_rate <= element.max_error_rate
            )
            
            if debug_mode:
                print(f"  Final result: errors={best_errors}, error_rate={error_rate:.4f}, success={success}")
            
            results.append(MatchResult(
                search_text=element.search_text,
                errors=best_errors,
                error_rate=error_rate,
                match_case=element.match_case,
                success=success
            ))
        else:
            if debug_mode:
                print(f"  No hypotheses found!")
            results.append(MatchResult(
                search_text=element.search_text,
                errors=-1,
                error_rate=1.0,
                match_case=element.match_case,
                success=False
            ))

    return results

def test_levenshtein_manually():
    """Test Levenshtein distance calculations manually"""
    print("\n" + "="*60)
    print("MANUAL LEVENSHTEIN DISTANCE TESTS")
    print("="*60)
    
    test_cases = [
        ("anothertext", "annothertext"),
        ("book", "boak"),
        ("superspecial_secrett", "superspecial_secrett"),
    ]
    
    for pattern, found in test_cases:
        distance_result = distance.Levenshtein.distance(pattern, found)
        print(f"\nPattern: '{pattern}'")
        print(f"Found:   '{found}'")
        print(f"Distance: {distance_result}")
        
        # Character-by-character comparison
        print("Character comparison:")
        for i, (p_char, f_char) in enumerate(zip(pattern, found)):
            if p_char != f_char:
                print(f"  Position {i}: '{p_char}' != '{f_char}'")
        
        if len(pattern) != len(found):
            print(f"  Length mismatch: pattern={len(pattern)}, found={len(found)}")

def main():
    """Main test function"""
    print("FUZZY TEXT SEARCH DEBUG SCRIPT")
    print("="*50)
    
    # Test elements
    elements = [
        StaticTextElement(search_text="SuperSpecial_secret",
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
    
    # # Test with debug mode ON
    # print("\n" + "="*60)
    # print("DEBUG MODE ON - Detailed search process")
    # print("="*60)
    # matches_debug = search_static_text_elements(elements, ocr_text, debug_mode=True)
    
    print("\n" + "="*60)
    print("DEBUG MODE OFF - Clean output")
    print("="*60)
    matches_clean = search_static_text_elements(elements, ocr_text, debug_mode=False)
    
    print("\n" + "="*50)
    print("FINAL RESULTS (Both modes should be identical)")
    print("="*50)
    
    for match in matches_clean:
        print(f"Search: '{match.search_text}' -> Errors: {match.errors}, Rate: {match.error_rate:.4f}, Success: {match.success}")
    
    # Manual Levenshtein tests
    test_levenshtein_manually()

if __name__ == "__main__":
    main()
