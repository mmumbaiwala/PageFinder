# PDF Processing Performance Optimization

This project implements comprehensive performance optimizations for PDF processing, including OCR text extraction and digital text extraction, with storage in LMDB databases.

## 🚀 Performance Improvements Implemented

### 1. **Parallel Processing**
- **ThreadPoolExecutor**: Processes multiple PDFs concurrently instead of sequentially
- **Configurable Workers**: Adjustable number of worker threads (default: 4-8 based on CPU cores)
- **Expected Improvement**: 3-6x faster processing on multi-core systems

### 2. **Memory Optimization**
- **Chunked Processing**: Processes pages in configurable chunks to manage memory usage
- **Automatic Cleanup**: Forces garbage collection when memory usage exceeds limits
- **Memory Monitoring**: Real-time memory usage tracking and cleanup triggers
- **Expected Improvement**: 30-50% reduction in peak memory usage

### 3. **Database Optimization**
- **Batch Operations**: Saves multiple pages in single database transactions
- **Reduced I/O**: Fewer database operations per document
- **Expected Improvement**: 20-40% faster database operations

### 4. **OCR Optimization**
- **Parallel Image Processing**: Multiple images processed simultaneously within each PDF
- **Batched OCR**: Processes images in configurable batches
- **Memory-Efficient**: Processes images in chunks to avoid memory overflow
- **Expected Improvement**: 2-4x faster OCR processing for PDFs with many images

### 5. **Caching & Incremental Processing**
- **File Hash Caching**: Stores file hashes to avoid recalculating unchanged files
- **Checkpoint System**: Resumes interrupted processing from where it left off
- **Smart Skipping**: Only processes new or changed files
- **Expected Improvement**: 90%+ faster for subsequent runs with unchanged files

### 6. **Configuration Management**
- **JSON Configuration**: Easy tuning of optimization parameters without code changes
- **Validation**: Automatic validation of configuration values
- **Hot-Reloading**: Configuration changes take effect immediately

## 📁 Files Overview

### Core Implementation Files
- **`process_pdfs_to_lmdb_optimized.py`** - Main optimized processing script
- **`text_preprocessing_optimized.py`** - Optimized text extraction functions
- **`lmdb_document_store.py`** - Enhanced LMDB storage with batch operations
- **`config_loader.py`** - Configuration management system

### Configuration & Benchmarking
- **`processing_config.json`** - Default optimization settings
- **`benchmark_performance.py`** - Performance comparison tool
- **`README_OPTIMIZATION.md`** - This documentation

### Original Files (for comparison)
- **`process_pdfs_to_lmdb.py`** - Original sequential implementation
- **`process_pdfs_to_lmdb_incremental.py`** - Original incremental implementation

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR
- **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### 3. Verify Installation
```bash
python config_loader.py
```

## 🚀 Quick Start

### Basic Usage (Optimized)
```python
from process_pdfs_to_lmdb_optimized import process_pdf_folder_optimized, ProcessingConfig

# Create configuration
config = ProcessingConfig(
    max_workers=4,           # Number of parallel workers
    batch_size=10,           # Pages per batch
    memory_limit_mb=1024,    # Memory limit before cleanup
    enable_ocr=True,         # Enable OCR processing
    enable_digital=True,     # Enable digital text extraction
    skip_existing=True       # Skip already processed files
)

# Process PDFs
process_pdf_folder_optimized(
    "path/to/pdf/folder",
    tesseract_path="path/to/tesseract.exe",
    config=config
)
```

### Command Line Usage
```bash
# Basic optimization (4 workers)
python process_pdfs_to_lmdb_optimized.py "path/to/pdfs" --tesseract "path/to/tesseract.exe"

# High-performance mode (8 workers, larger batches)
python process_pdfs_to_lmdb_optimized.py "path/to/pdfs" \
    --workers 8 \
    --batch-size 20 \
    --memory-limit 2048 \
    --tesseract "path/to/tesseract.exe"

# OCR-only mode (skip digital text)
python process_pdfs_to_lmdb_optimized.py "path/to/pdfs" \
    --no-digital \
    --tesseract "path/to/tesseract.exe"
```

## ⚙️ Configuration

### Configuration File (`processing_config.json`)
```json
{
  "performance": {
    "max_workers": 4,
    "batch_size": 10,
    "memory_limit_mb": 1024,
    "ocr_batch_size": 5,
    "page_chunk_size": 10
  },
  "features": {
    "enable_ocr": true,
    "enable_digital": true,
    "skip_existing": true,
    "enable_caching": true,
    "enable_checkpointing": true
  },
  "ocr": {
    "tesseract_config": "--psm 4",
    "timeout_seconds": 30,
    "max_ocr_workers": 2
  }
}
```

### Configuration via Code
```python
from config_loader import ConfigLoader

# Load configuration
config = ConfigLoader("custom_config.json")

# Get specific settings
max_workers = config.get("performance", "max_workers", 4)
memory_limit = config.get("performance", "memory_limit_mb", 1024)

# Update settings
config.set("performance", "max_workers", 8)
config.save_config()
```

## 📊 Performance Benchmarking

### Run Comprehensive Benchmark
```bash
# Benchmark all implementations
python benchmark_performance.py "path/to/test/pdfs" \
    --tesseract "path/to/tesseract.exe" \
    --workers 1 2 4 8 \
    --output "my_benchmark_results.json"
```

### Benchmark Results Include
- **Execution Time**: Total processing time per implementation
- **Memory Usage**: Peak memory usage and memory efficiency
- **Throughput**: Files processed per second
- **Speedup Factor**: Performance improvement over baseline
- **System Information**: CPU, memory, and platform details

### Expected Results
- **Sequential (Old)**: Baseline performance
- **Incremental (Old)**: 10-20% improvement
- **Optimized (1 worker)**: 20-40% improvement
- **Optimized (4 workers)**: 3-6x improvement
- **Optimized (8 workers)**: 4-8x improvement (depending on system)

## 🔧 Tuning for Your System

### High-Performance Systems (16+ cores, 32GB+ RAM)
```json
{
  "performance": {
    "max_workers": 12,
    "batch_size": 20,
    "memory_limit_mb": 4096,
    "ocr_batch_size": 10
  }
}
```

### Memory-Constrained Systems (8GB RAM)
```json
{
  "performance": {
    "max_workers": 2,
    "batch_size": 5,
    "memory_limit_mb": 512,
    "ocr_batch_size": 3
  }
}
```

### OCR-Heavy Workloads (Many images per PDF)
```json
{
  "performance": {
    "max_workers": 4,
    "batch_size": 15,
    "ocr_batch_size": 8
  },
  "ocr": {
    "max_ocr_workers": 4,
    "timeout_seconds": 60
  }
}
```

## 🐛 Troubleshooting

### Common Issues

#### 1. **Memory Errors**
- Reduce `memory_limit_mb` in configuration
- Decrease `batch_size` and `ocr_batch_size`
- Reduce `max_workers`

#### 2. **OCR Timeouts**
- Increase `ocr.timeout_seconds` in configuration
- Reduce `ocr.max_ocr_workers`
- Check Tesseract installation

#### 3. **Slow Performance**
- Increase `max_workers` (up to CPU core count)
- Increase `batch_size` for larger datasets
- Ensure `skip_existing` is enabled for repeated runs

#### 4. **Database Errors**
- Check available disk space
- Verify LMDB permissions
- Increase `map_size_bytes` in LmdbDocumentStore

### Performance Monitoring
```python
from text_preprocessing_optimized import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.start_operation("pdf_processing")

# ... process PDFs ...

monitor.end_operation("pdf_processing", {"files_processed": 100})
print("Performance:", monitor.get_summary())
```

## 📈 Scaling Guidelines

### Small Datasets (< 100 PDFs)
- Use default configuration
- 2-4 workers sufficient

### Medium Datasets (100-1000 PDFs)
- 4-8 workers recommended
- Enable all optimizations
- Use checkpointing for reliability

### Large Datasets (1000+ PDFs)
- 8-16 workers (if system supports)
- Increase batch sizes
- Monitor memory usage closely
- Consider processing in chunks

### Enterprise Scale (10000+ PDFs)
- Distributed processing across multiple machines
- Database sharding
- Load balancing
- Custom optimization for specific PDF types

## 🔮 Future Enhancements

### Planned Optimizations
- **GPU Acceleration**: CUDA-based OCR processing
- **Streaming Processing**: Process PDFs without loading entire files
- **Distributed Processing**: Multi-machine processing support
- **Advanced Caching**: Redis-based distributed caching
- **Machine Learning**: Smart OCR preprocessing and post-processing

### Contributing
1. Fork the repository
2. Create feature branch
3. Implement optimizations
4. Add benchmarks
5. Submit pull request

## 📞 Support

For questions or issues:
1. Check this documentation
2. Review benchmark results
3. Examine configuration settings
4. Check system requirements
5. Open an issue with detailed information

---

**Happy Optimizing! 🚀**
