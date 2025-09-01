#!/usr/bin/env python3
"""
PageFinder Quick Start Script
============================

This script provides a quick way to test and use your PageFinder system.
Run this to quickly verify everything is working and process some sample PDFs.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step, description):
    """Print a step with description"""
    print(f"\n{step} {description}")
    print("-" * 50)

def run_command(command, description, check_output=False):
    """Run a command and show results"""
    print(f"Running: {command}")
    
    try:
        if check_output:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print("✅ Success!")
                if result.stdout:
                    print(f"Output: {result.stdout[:200]}...")
            else:
                print(f"❌ Failed: {result.stderr[:200]}...")
            return result.returncode == 0
        else:
            result = subprocess.run(command, shell=True, timeout=120)
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
        return False
    except Exception as e:
        print(f"💥 Error: {e}")
        return False

def check_sample_data():
    """Check if sample data exists"""
    sample_path = Path("SampleData")
    if sample_path.exists() and any(sample_path.glob("*.pdf")):
        pdf_count = len(list(sample_path.glob("*.pdf")))
        print(f"✅ Found {pdf_count} PDF files in SampleData/")
        return True
    else:
        print("❌ No sample PDFs found in SampleData/")
        print("Please add some PDF files to the SampleData folder")
        return False

def get_tesseract_path():
    """Get Tesseract path or ask user"""
    # Common Windows paths
    common_paths = [
        r"C:\Users\mmumbaiwala\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"✅ Found Tesseract at: {path}")
            return path
    
    print("❌ Tesseract not found in common locations")
    print("Please provide the path to your Tesseract executable:")
    user_path = input("Tesseract path: ").strip().strip('"')
    
    if user_path and os.path.exists(user_path):
        print(f"✅ Using Tesseract at: {user_path}")
        return user_path
    else:
        print("❌ Invalid Tesseract path")
        return None

def main():
    """Main quick start function"""
    print_header("PageFinder Quick Start")
    
    print("This script will quickly test your PageFinder system and process sample PDFs.")
    print("Make sure you have:")
    print("  • Python 3.8+ installed")
    print("  • Dependencies installed (uv sync)")
    print("  • Tesseract OCR installed")
    print("  • Some PDF files in the SampleData folder")
    
    # Step 1: Check sample data
    print_step("1️⃣", "Checking Sample Data")
    if not check_sample_data():
        print("\n⚠️  Please add PDF files to SampleData/ folder and run again")
        return
    
    # Step 2: Get Tesseract path
    print_step("2️⃣", "Locating Tesseract OCR")
    tesseract_path = get_tesseract_path()
    if not tesseract_path:
        print("\n❌ Cannot proceed without Tesseract OCR")
        print("Please install Tesseract and run this script again")
        return
    
    # Step 3: Test system components
    print_step("3️⃣", "Testing System Components")
    print("Running quick component tests...")
    
    test_commands = [
        ("Configuration System", "uv run python config_loader.py"),
        ("Text Processing", "uv run python text_preprocessing_optimized.py"),
        ("Database Operations", "uv run python lmdb_document_store.py")
    ]
    
    all_tests_passed = True
    for name, command in test_commands:
        print(f"\n🧪 Testing {name}...")
        if not run_command(command, name, check_output=True):
            all_tests_passed = False
    
    if not all_tests_passed:
        print("\n⚠️  Some component tests failed. Please check the errors above.")
        print("You may need to run: uv sync")
        return
    
    # Step 4: Quick performance test
    print_step("4️⃣", "Quick Performance Test")
    print("Running a quick performance benchmark...")
    
    benchmark_cmd = f'uv run python benchmark_performance.py "SampleData" --tesseract "{tesseract_path}" --workers 4'
    if run_command(benchmark_cmd, "Performance Benchmark"):
        print("✅ Performance test completed!")
    else:
        print("⚠️  Performance test failed, but continuing...")
    
    # Step 5: Process sample PDFs
    print_step("5️⃣", "Processing Sample PDFs")
    print("Processing PDFs with optimized system...")
    
    process_cmd = f'uv run python process_pdfs_to_lmdb_optimized.py "SampleData" --tesseract "{tesseract_path}" --workers 4'
    if run_command(process_cmd, "PDF Processing"):
        print("✅ PDF processing completed!")
    else:
        print("❌ PDF processing failed")
        return
    
    # Step 6: Show results
    print_step("6️⃣", "Results & Next Steps")
    print("🎉 Your PageFinder system is working correctly!")
    
    print("\n📊 What was processed:")
    print("  • Sample PDFs extracted and stored in database")
    print("  • Text extracted using OCR and digital methods")
    print("  • Performance benchmark completed")
    
    print("\n🚀 Next steps:")
    print("  1. Process your own PDF collection:")
    print(f"     uv run python process_pdfs_to_lmdb_optimized.py \"your_pdf_folder\" --tesseract \"{tesseract_path}\" --workers 4")
    
    print("  2. Customize settings in processing_config.json")
    
    print("  3. Run comprehensive tests:")
    print("     uv run python test_optimizations.py")
    
    print("  4. Check performance with different worker counts:")
    print(f"     uv run python benchmark_performance.py \"your_pdf_folder\" --tesseract \"{tesseract_path}\" --workers 1 2 4 8")
    
    print("\n📚 Documentation:")
    print("  • README.md - Complete project overview")
    print("  • COMMANDS_REFERENCE.md - All commands explained")
    print("  • README_OPTIMIZATION.md - Optimization details")
    
    print("\n" + "=" * 60)
    print("🎯 Quick Start Complete! Your PageFinder system is ready!")
    print("=" * 60)

if __name__ == "__main__":
    main()
