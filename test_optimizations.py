#!/usr/bin/env python3
"""
Test script to verify all optimization components are working correctly.
"""

import time
from pathlib import Path

def test_imports():
    """Test that all modules can be imported successfully"""
    print("🧪 Testing imports...")
    
    try:
        from config_loader import ConfigLoader
        print("  ✅ ConfigLoader imported successfully")
    except ImportError as e:
        print(f"  ❌ ConfigLoader import failed: {e}")
        return False
    
    try:
        from text_preprocessing_optimized import PerformanceMonitor
        print("  ✅ PerformanceMonitor imported successfully")
    except ImportError as e:
        print(f"  ❌ PerformanceMonitor import failed: {e}")
        return False
    
    try:
        from process_pdfs_to_lmdb_optimized import ProcessingConfig
        print("  ✅ ProcessingConfig imported successfully")
    except ImportError as e:
        print(f"  ❌ ProcessingConfig import failed: {e}")
        return False
    
    try:
        from lmdb_document_store import LmdbDocumentStore
        print("  ✅ LmdbDocumentStore imported successfully")
    except ImportError as e:
        print(f"  ❌ LmdbDocumentStore import failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading and saving"""
    print("\n⚙️  Testing configuration system...")
    
    try:
        from config_loader import ConfigLoader
        
        # Test default config
        config = ConfigLoader()
        print(f"  ✅ Default config loaded: {config.get('performance', 'max_workers')} workers")
        
        # Test config modification
        original_workers = config.get('performance', 'max_workers')
        config.set('performance', 'max_workers', 8)
        print(f"  ✅ Config modified: {original_workers} → 8 workers")
        
        # Test config saving
        config.save_config()
        print("  ✅ Config saved successfully")
        
        # Test config reloading
        config2 = ConfigLoader()
        new_workers = config2.get('performance', 'max_workers')
        print(f"  ✅ Config reloaded: {new_workers} workers")
        
        # Restore original
        config2.set('performance', 'max_workers', original_workers)
        config2.save_config()
        print(f"  ✅ Original config restored: {original_workers} workers")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_performance_monitor():
    """Test performance monitoring system"""
    print("\n📊 Testing performance monitoring...")
    
    try:
        from text_preprocessing_optimized import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Test timing
        monitor.start_operation("test_operation")
        time.sleep(0.1)  # Simulate work
        monitor.end_operation("test_operation", {"test_data": "success"})
        
        summary = monitor.get_summary()
        print(f"  ✅ Performance monitor working: {summary}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance monitor test failed: {e}")
        return False

def test_processing_config():
    """Test processing configuration"""
    print("\n🔧 Testing processing configuration...")
    
    try:
        from process_pdfs_to_lmdb_optimized import ProcessingConfig
        
        # Test default config
        config = ProcessingConfig()
        print(f"  ✅ Default config: {config.max_workers} workers, {config.batch_size} batch size")
        
        # Test custom config
        custom_config = ProcessingConfig(
            max_workers=6,
            batch_size=15,
            memory_limit_mb=2048,
            enable_ocr=True,
            enable_digital=False
        )
        print(f"  ✅ Custom config: {custom_config.max_workers} workers, OCR: {custom_config.enable_ocr}, Digital: {custom_config.enable_digital}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Processing config test failed: {e}")
        return False

def test_lmdb_store():
    """Test LMDB document store"""
    print("\n🗄️  Testing LMDB document store...")
    
    try:
        from lmdb_document_store import LmdbDocumentStore
        import tempfile
        import os
        
        # Create temporary database
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_db.lmdb")
            
            # Test database creation
            db = LmdbDocumentStore(db_path)
            print("  ✅ Database created successfully")
            
            # Test metadata saving
            db.save_document_metadata("test_doc", "/test/path.pdf", "test.pdf", {"pages": 5})
            print("  ✅ Metadata saved successfully")
            
            # Test metadata retrieval
            metadata = db.get_document_metadata("test_doc")
            print(f"  ✅ Metadata retrieved: {metadata['pages']} pages")
            
            # Test batch page saving
            page_data = [("Digital text 1", "OCR text 1"), ("Digital text 2", "OCR text 2")]
            db.save_page_texts_batch("test_doc", page_data)
            print("  ✅ Batch page saving successful")
            
            # Test page retrieval
            digital_text = db.get_page_digital_text("test_doc", 1)
            ocr_text = db.get_page_ocr_text("test_doc", 1)
            print(f"  ✅ Page 1 retrieved - Digital: {len(digital_text)} chars, OCR: {len(ocr_text)} chars")
            
            # Test document listing
            docs = db.list_all_docs()
            print(f"  ✅ Documents listed: {docs}")
            
            # Clean up
            db.close()
            print("  ✅ Database closed successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ LMDB store test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 PDF Processing Optimization Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_performance_monitor,
        test_processing_config,
        test_lmdb_store
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Optimization system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
