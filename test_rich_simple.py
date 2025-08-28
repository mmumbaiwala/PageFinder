from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_rich():
    """Simple test of rich library functionality."""
    
    # Test basic console output
    console.print("Hello from Rich!", style="bold blue")
    
    # Test panel
    console.print(Panel("This is a test panel", style="green"))
    
    # Test table
    table = Table(title="Test Table")
    table.add_column("Name", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Test 1", "Value 1")
    table.add_row("Test 2", "Value 2")
    console.print(table)
    
    print("Rich library test completed!")

if __name__ == "__main__":
    test_rich()
