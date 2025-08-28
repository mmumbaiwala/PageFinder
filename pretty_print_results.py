from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich import box
from element_search_core import MatchResult, StaticTextElement
from typing import List
import re

console = Console()

def pretty_print_search_results(elements: List[StaticTextElement], 
                              results: List[MatchResult], 
                              page_number: int = None,
                              show_details: bool = True):
    """
    Pretty print search results using rich library with colors and formatting.
    
    Args:
        elements: List of StaticTextElement that were searched for
        results: List of MatchResult from the search
        page_number: Optional page number for context
        show_details: Whether to show detailed match information
    """
    
    # Header
    if page_number is not None:
        header = f"🔍 Search Results - Page {page_number}"
    else:
        header = "🔍 Search Results"
    
    console.print(Panel(header, style="bold blue", box=box.DOUBLE))
    
    # Summary table
    summary_table = Table(title="📊 Search Summary", box=box.ROUNDED)
    summary_table.add_column("Element", style="cyan", no_wrap=True)
    summary_table.add_column("Status", style="bold")
    summary_table.add_column("Matched Text", style="green")
    summary_table.add_column("Errors", style="yellow")
    summary_table.add_column("Error Rate", style="magenta")
    
    for i, (element, result) in enumerate(zip(elements, results)):
        # Status indicator
        if result.success:
            status = "✅ PASS"
            status_style = "bold green"
        else:
            status = "❌ FAIL"
            status_style = "bold red"
        
        # Error rate formatting
        if result.errors >= 0:
            error_rate_pct = f"{result.error_rate * 100:.1f}%"
            errors_str = str(result.errors)
        else:
            error_rate_pct = "N/A"
            errors_str = "N/A"
        
        # Truncate long matched text
        matched_display = result.matched_string[:50] + "..." if len(result.matched_string) > 50 else result.matched_string
        if not matched_display:
            matched_display = "[dim]No match[/dim]"
        
        summary_table.add_row(
            element.search_text,
            Text(status, style=status_style),
            matched_display,
            errors_str,
            error_rate_pct
        )
    
    console.print(summary_table)
    
    if show_details:
        # Detailed results for each element
        for i, (element, result) in enumerate(zip(elements, results)):
            console.print()  # Spacing
            
            # Element header
            element_header = f"Element {i+1}: '{element.search_text}'"
            if element.match_case:
                element_header += " (Case Sensitive)"
            else:
                element_header += " (Case Insensitive)"
            
            console.print(Panel(element_header, style="bold cyan", box=box.SIMPLE))
            
            # Result details
            if result.success:
                if result.errors == 0:
                    # Exact match
                    console.print(f"  🎯 [bold green]Exact Match Found![/bold green]")
                    console.print(f"  📝 Matched: [green]'{result.matched_string}'[/green]")
                else:
                    # Fuzzy match
                    console.print(f"  🎯 [bold green]Fuzzy Match Found![/bold green]")
                    console.print(f"  📝 Matched: [green]'{result.matched_string}'[/green]")
                    console.print(f"  ❌ Errors: [yellow]{result.errors}[/yellow]")
                    console.print(f"  📊 Error Rate: [magenta]{result.error_rate:.4f} ({result.error_rate*100:.1f}%)[/magenta]")
                
                # Show tolerance settings
                tolerance_info = []
                if element.max_errors is not None:
                    tolerance_info.append(f"Max Errors: [cyan]{element.max_errors}[/cyan]")
                if element.max_error_rate is not None:
                    tolerance_info.append(f"Max Error Rate: [cyan]{element.max_error_rate:.4f} ({element.max_error_rate*100:.1f}%)[/cyan]")
                
                if tolerance_info:
                    console.print(f"  ⚙️  Tolerance: {' | '.join(tolerance_info)}")
                
            else:
                # Failed match
                if result.errors == -1:
                    console.print(f"  ❌ [bold red]No Match Found[/bold red]")
                    console.print(f"  💡 The search pattern '{element.search_text}' was not found in the text")
                else:
                    console.print(f"  ❌ [bold red]Match Failed Tolerance Check[/bold red]")
                    console.print(f"  📝 Best Match: [dim]'{result.matched_string}'[/dim]")
                    console.print(f"  ❌ Errors: [yellow]{result.errors}[/yellow]")
                    console.print(f"  📊 Error Rate: [magenta]{result.error_rate:.4f} ({result.error_rate*100:.1f}%)[/magenta]")
                    
                    # Show why it failed
                    failure_reasons = []
                    if element.max_errors is not None and result.errors > element.max_errors:
                        failure_reasons.append(f"Errors ({result.errors}) > Max ({element.max_errors})")
                    if element.max_error_rate is not None and result.error_rate > element.max_error_rate:
                        failure_reasons.append(f"Error Rate ({result.error_rate:.4f}) > Max ({element.max_error_rate:.4f})")
                    
                    if failure_reasons:
                        console.print(f"  🚫 Failed: [red]{' | '.join(failure_reasons)}[/red]")
    
    # Footer
    console.print()
    total_elements = len(elements)
    passed_elements = sum(1 for r in results if r.success)
    failed_elements = total_elements - passed_elements
    
    footer_text = f"📈 Results: {passed_elements}/{total_elements} elements passed"
    if failed_elements > 0:
        footer_text += f" ({failed_elements} failed)"
    
    console.print(Panel(footer_text, style="bold blue", box=box.SIMPLE))


def pretty_print_page_search(elements: List[StaticTextElement], 
                           text_pages: List[str], 
                           page_range: tuple = None,
                           show_details: bool = True):
    """
    Pretty print search results across multiple pages.
    
    Args:
        elements: List of StaticTextElement to search for
        text_pages: List of text pages to search
        page_range: Optional tuple (start, end) for page range
        show_details: Whether to show detailed results
    """
    from element_search_core import search_static_text_elements
    
    if page_range:
        start_page, end_page = page_range
        pages_to_search = text_pages[start_page:end_page]
        page_indices = range(start_page, end_page)
    else:
        pages_to_search = text_pages
        page_indices = range(len(text_pages))
    
    console.print(Panel(f"🔍 Multi-Page Search: {len(pages_to_search)} pages", 
                       style="bold blue", box=box.DOUBLE))
    
    for page_idx, (page_text, page_num) in enumerate(zip(pages_to_search, page_indices)):
        # Skip empty pages
        if not page_text.strip():
            continue
            
        # Run search for this page
        results = search_static_text_elements(elements, page_text, debug_mode=False)
        
        # Check if any elements were found on this page
        if any(result.success for result in results):
            pretty_print_search_results(elements, results, page_num, show_details)
            
            # Show page preview if there are matches
            if show_details:
                console.print()
                page_preview = page_text[:200] + "..." if len(page_text) > 200 else page_text
                console.print(Panel(f"📄 Page {page_num} Preview:\n[dim]{page_preview}[/dim]", 
                                  style="dim", box=box.SIMPLE))
        
        # Add separator between pages (except for last page)
        if page_idx < len(pages_to_search) - 1:
            console.print("\n" + "─" * 80 + "\n")


# Example usage and testing
if __name__ == "__main__":
    from element_search_core import StaticTextElement, search_static_text_elements
    
    # Test elements
    elements = [
        StaticTextElement(search_text="COM", max_errors=1, max_error_rate=0.3, match_case=False),
        StaticTextElement(search_text="Relationship Name", max_errors=2, match_case=True),
        StaticTextElement(search_text="sample", max_error_rate=0.4, match_case=False),
    ]
    
    # Test text
    test_text = "This is a CQM message with some Relationship Nme text to search in. Example"
    
    print("Testing Pretty Print Function")
    print("=" * 50)
    
    # Run search
    results = search_static_text_elements(elements, test_text, debug_mode=False)
    
    # Pretty print results
    pretty_print_search_results(elements, results, show_details=True)
