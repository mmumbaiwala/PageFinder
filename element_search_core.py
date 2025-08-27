#!/usr/bin/env python3
"""
Core fuzzy text search functionality for OCR text matching.
Contains the main search algorithm and data structures.
"""

from rapidfuzz import fuzz, distance
from attrs import define, field, validators
from typing import Optional, Tuple

@define
class StaticTextElement:
    """Defines a search pattern with error tolerance settings."""
    search_text: str = field(validator=validators.instance_of(str))
    match_case: bool = field(default=False, validator=validators.instance_of(bool))
    max_errors: Optional[int] = field(default=None, validator=validators.optional(validators.instance_of(int)))
    max_error_rate: Optional[float] = field(default=None, validator=validators.optional(validators.instance_of(float)))
    
    def __attrs_post_init__(self):
        """Validate that at least one error condition is provided."""
        if self.max_errors is None and self.max_error_rate is None:
            raise ValueError("At least one of max_errors or max_error_rate must be provided")

@define
class MatchResult:
    """Stores the result of a fuzzy text search."""
    matched_string: str = field(validator=validators.instance_of(str))
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
        debug_mode: If True, prints detailed search process. If False, only final results
    
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
                matched_string=pattern,
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
            
            # Check success based on provided conditions
            # If both max_errors and max_error_rate are provided, both must be satisfied
            # If only one is provided, only that condition is checked
            # If neither is provided, validation error would have occurred during object creation
            success = True
            
            # Check max_errors if it's provided (not None)
            if hasattr(element, 'max_errors') and element.max_errors is not None:
                success = success and (best_errors <= element.max_errors)
            
            # Check max_error_rate if it's provided (not None)
            if hasattr(element, 'max_error_rate') and element.max_error_rate is not None:
                success = success and (error_rate <= element.max_error_rate)
            
            if debug_mode:
                print(f"  Final result: errors={best_errors}, error_rate={error_rate:.4f}, success={success}")
            
            results.append(MatchResult(
                matched_string=best_substring,
                errors=best_errors,
                error_rate=error_rate,
                match_case=element.match_case,
                success=success
            ))
        else:
            if debug_mode:
                print(f"  No hypotheses found!")
            results.append(MatchResult(
                matched_string="",
                errors=-1,
                error_rate=1.0,
                match_case=element.match_case,
                success=False
            ))

    return results


if __name__ == "__main__":
    """Basic test when run directly"""
    # Simple test elements - demonstrating different configurations
    elements = [
        # Both conditions provided (original behavior)
        StaticTextElement(search_text="test",
                          max_errors=1,
                          max_error_rate=0.3,
                          match_case=False),
        # Only max_errors provided
        StaticTextElement(search_text="example",
                          max_errors=2,
                          match_case=True),
        # Only max_error_rate provided
        StaticTextElement(search_text="sample",
                          max_error_rate=0.4,
                          match_case=False),
    ]
    
    # Simple test text
    test_text = "This is a tesst message with some text to search in. Example"
    
    print("Basic test of fuzzy search core module")
    print("="*40)
    
    # Run search
    results = search_static_text_elements(elements, test_text, debug_mode=False)
    
    # Display results
    for i, result in enumerate(results):
        if result.errors >= 0:
            error_rate_pct = result.error_rate * 100
            print(f"Search: '{elements[i].search_text}' -> Matched: '{result.matched_string}', Errors: {result.errors}, Error Rate: {error_rate_pct:.1f}%, Success: {result.success}")
        else:
            print(f"Search: '{elements[i].search_text}' -> No match found, Success: {result.success}")
    
    print("Core module test completed successfully!")
