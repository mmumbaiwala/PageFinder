import os
import time
import psutil
import gc
import json
from pathlib import Path
from typing import Dict, List, Any
import statistics
from datetime import datetime
import argparse

# Import both old and optimized versions
from process_pdfs_to_lmdb import process_pdf_folder as process_pdf_folder_old
from process_pdfs_to_lmdb_incremental import process_pdf_folder_incremental as process_pdf_folder_incremental_old
from process_pdfs_to_lmdb_optimized import process_pdf_folder_optimized, ProcessingConfig
from config_loader import ConfigLoader


class PerformanceBenchmark:
    """Comprehensive performance benchmarking for PDF processing implementations"""
    
    def __init__(self, test_folder: str, output_file: str = "benchmark_results.json"):
        self.test_folder = test_folder
        self.output_file = output_file
        self.results = {}
        self.process = psutil.Process()
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage in MB"""
        memory_info = self.process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": self.process.memory_percent()
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmarking context"""
        return {
            "cpu_count": os.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "platform": os.name,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
        }
    
    def cleanup_database(self, db_path: str):
        """Remove test database files"""
        try:
            if os.path.exists(db_path):
                import shutil
                shutil.rmtree(db_path)
                print(f"  🗑️  Cleaned up database: {db_path}")
        except Exception as e:
            print(f"  ⚠️  Could not clean up database {db_path}: {e}")
    
    def benchmark_old_sequential(self, tesseract_path: str = None) -> Dict[str, Any]:
        """Benchmark the old sequential processing implementation"""
        print("\n🔄 Benchmarking OLD Sequential Implementation...")
        
        db_path = "benchmark_old_sequential.lmdb"
        self.cleanup_database(db_path)
        
        # Measure memory before
        memory_before = self.get_memory_usage()
        
        # Start timing
        start_time = time.time()
        start_cpu = psutil.cpu_percent(interval=1)
        
        try:
            # Run old implementation
            process_pdf_folder_old(self.test_folder, db_path, tesseract_path)
            
            # Measure memory after
            memory_after = self.get_memory_usage()
            
            # Calculate metrics
            end_time = time.time()
            end_cpu = psutil.cpu_percent(interval=1)
            
            execution_time = end_time - start_time
            memory_peak = max(memory_before["rss_mb"], memory_after["rss_mb"])
            memory_increase = memory_after["rss_mb"] - memory_before["rss_mb"]
            
            # Count processed files
            pdf_files = list(Path(self.test_folder).glob("*.pdf"))
            
            result = {
                "implementation": "old_sequential",
                "execution_time_seconds": execution_time,
                "files_processed": len(pdf_files),
                "throughput_files_per_second": len(pdf_files) / execution_time if execution_time > 0 else 0,
                "memory_before_mb": memory_before["rss_mb"],
                "memory_after_mb": memory_after["rss_mb"],
                "memory_peak_mb": memory_peak,
                "memory_increase_mb": memory_increase,
                "cpu_usage_start": start_cpu,
                "cpu_usage_end": end_cpu,
                "database_size_mb": self.get_database_size(db_path),
                "success": True
            }
            
            print(f"  ✅ Completed in {execution_time:.2f}s")
            print(f"  📊 Memory: {memory_before['rss_mb']:.1f}MB → {memory_after['rss_mb']:.1f}MB (peak: {memory_peak:.1f}MB)")
            print(f"  🚀 Throughput: {result['throughput_files_per_second']:.2f} files/sec")
            
        except Exception as e:
            result = {
                "implementation": "old_sequential",
                "execution_time_seconds": time.time() - start_time,
                "error": str(e),
                "success": False
            }
            print(f"  ❌ Failed: {e}")
        
        finally:
            self.cleanup_database(db_path)
        
        return result
    
    def benchmark_old_incremental(self, tesseract_path: str = None) -> Dict[str, Any]:
        """Benchmark the old incremental processing implementation"""
        print("\n🔄 Benchmarking OLD Incremental Implementation...")
        
        db_path = "benchmark_old_incremental.lmdb"
        self.cleanup_database(db_path)
        
        # Measure memory before
        memory_before = self.get_memory_usage()
        
        # Start timing
        start_time = time.time()
        start_cpu = psutil.cpu_percent(interval=1)
        
        try:
            # Run old incremental implementation
            process_pdf_folder_incremental_old(self.test_folder, db_path, tesseract_path)
            
            # Measure memory after
            memory_after = self.get_memory_usage()
            
            # Calculate metrics
            end_time = time.time()
            end_cpu = psutil.cpu_percent(interval=1)
            
            execution_time = end_time - start_time
            memory_peak = max(memory_before["rss_mb"], memory_after["rss_mb"])
            memory_increase = memory_after["rss_mb"] - memory_before["rss_mb"]
            
            # Count processed files
            pdf_files = list(Path(self.test_folder).glob("*.pdf"))
            
            result = {
                "implementation": "old_incremental",
                "execution_time_seconds": execution_time,
                "files_processed": len(pdf_files),
                "throughput_files_per_second": len(pdf_files) / execution_time if execution_time > 0 else 0,
                "memory_before_mb": memory_before["rss_mb"],
                "memory_after_mb": memory_after["rss_mb"],
                "memory_peak_mb": memory_peak,
                "memory_increase_mb": memory_increase,
                "cpu_usage_start": start_cpu,
                "cpu_usage_end": end_cpu,
                "database_size_mb": self.get_database_size(db_path),
                "success": True
            }
            
            print(f"  ✅ Completed in {execution_time:.2f}s")
            print(f"  📊 Memory: {memory_before['rss_mb']:.1f}MB → {memory_after['rss_mb']:.1f}MB (peak: {memory_peak:.1f}MB)")
            print(f"  🚀 Throughput: {result['throughput_files_per_second']:.2f} files/sec")
            
        except Exception as e:
            result = {
                "implementation": "old_incremental",
                "execution_time_seconds": time.time() - start_time,
                "error": str(e),
                "success": False
            }
            print(f"  ❌ Failed: {e}")
        
        finally:
            self.cleanup_database(db_path)
        
        return result
    
    def benchmark_optimized(self, config: ProcessingConfig, tesseract_path: str = None) -> Dict[str, Any]:
        """Benchmark the optimized implementation with given configuration"""
        print(f"\n🚀 Benchmarking OPTIMIZED Implementation ({config.max_workers} workers)...")
        
        db_path = f"benchmark_optimized_{config.max_workers}workers.lmdb"
        self.cleanup_database(db_path)
        
        # Measure memory before
        memory_before = self.get_memory_usage()
        
        # Start timing
        start_time = time.time()
        start_cpu = psutil.cpu_percent(interval=1)
        
        try:
            # Run optimized implementation
            process_pdf_folder_optimized(self.test_folder, db_path, tesseract_path, config)
            
            # Measure memory after
            memory_after = self.get_memory_usage()
            
            # Calculate metrics
            end_time = time.time()
            end_cpu = psutil.cpu_percent(interval=1)
            
            execution_time = end_time - start_time
            memory_peak = max(memory_before["rss_mb"], memory_after["rss_mb"])
            memory_increase = memory_after["rss_mb"] - memory_before["rss_mb"]
            
            # Count processed files
            pdf_files = list(Path(self.test_folder).glob("*.pdf"))
            
            result = {
                "implementation": f"optimized_{config.max_workers}workers",
                "config": {
                    "max_workers": config.max_workers,
                    "batch_size": config.batch_size,
                    "memory_limit_mb": config.memory_limit_mb,
                    "enable_ocr": config.enable_ocr,
                    "enable_digital": config.enable_digital
                },
                "execution_time_seconds": execution_time,
                "files_processed": len(pdf_files),
                "throughput_files_per_second": len(pdf_files) / execution_time if execution_time > 0 else 0,
                "memory_before_mb": memory_before["rss_mb"],
                "memory_after_mb": memory_after["rss_mb"],
                "memory_peak_mb": memory_peak,
                "memory_increase_mb": memory_increase,
                "cpu_usage_start": start_cpu,
                "cpu_usage_end": end_cpu,
                "database_size_mb": self.get_database_size(db_path),
                "success": True
            }
            
            print(f"  ✅ Completed in {execution_time:.2f}s")
            print(f"  📊 Memory: {memory_before['rss_mb']:.1f}MB → {memory_after['rss_mb']:.1f}MB (peak: {memory_peak:.1f}MB)")
            print(f"  🚀 Throughput: {result['throughput_files_per_second']:.2f} files/sec")
            
        except Exception as e:
            result = {
                "implementation": f"optimized_{config.max_workers}workers",
                "config": {
                    "max_workers": config.max_workers,
                    "batch_size": config.batch_size,
                    "memory_limit_mb": config.memory_limit_mb
                },
                "execution_time_seconds": time.time() - start_time,
                "error": str(e),
                "success": False
            }
            print(f"  ❌ Failed: {e}")
        
        finally:
            self.cleanup_database(db_path)
        
        return result
    
    def get_database_size(self, db_path: str) -> float:
        """Get database size in MB"""
        try:
            if os.path.exists(db_path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(db_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                return total_size / 1024 / 1024  # Convert to MB
        except Exception:
            pass
        return 0.0
    
    def run_comprehensive_benchmark(self, tesseract_path: str = None, 
                                   worker_configs: List[int] = None) -> Dict[str, Any]:
        """Run comprehensive benchmark comparing all implementations"""
        print("=" * 80)
        print("🚀 COMPREHENSIVE PDF PROCESSING PERFORMANCE BENCHMARK")
        print("=" * 80)
        
        if worker_configs is None:
            worker_configs = [1, 2, 4, 8]
        
        # Get system info
        system_info = self.get_system_info()
        print(f"System: {system_info['cpu_count']} CPUs, {system_info['memory_total_gb']:.1f}GB RAM")
        print(f"Test folder: {self.test_folder}")
        print(f"PDF files found: {len(list(Path(self.test_folder).glob('*.pdf')))}")
        
        # Run benchmarks
        benchmark_results = []
        
        # Benchmark old implementations
        benchmark_results.append(self.benchmark_old_sequential(tesseract_path))
        benchmark_results.append(self.benchmark_old_incremental(tesseract_path))
        
        # Benchmark optimized implementations with different worker counts
        for worker_count in worker_configs:
            config = ProcessingConfig(
                max_workers=worker_count,
                batch_size=10,
                memory_limit_mb=1024,
                enable_ocr=True,
                enable_digital=True,
                skip_existing=True
            )
            benchmark_results.append(self.benchmark_optimized(config, tesseract_path))
        
        # Compile results
        self.results = {
            "benchmark_date": datetime.now().isoformat(),
            "system_info": system_info,
            "test_folder": self.test_folder,
            "pdf_count": len(list(Path(self.test_folder).glob("*.pdf"))),
            "benchmarks": benchmark_results,
            "summary": self._generate_summary(benchmark_results)
        }
        
        # Save results
        self._save_results()
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    def _generate_summary(self, benchmark_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from benchmark results"""
        successful_results = [r for r in benchmark_results if r.get("success", False)]
        
        if not successful_results:
            return {"error": "No successful benchmarks"}
        
        # Performance comparison
        fastest = min(successful_results, key=lambda x: x.get("execution_time_seconds", float('inf')))
        slowest = max(successful_results, key=lambda x: x.get("execution_time_seconds", 0))
        
        # Memory comparison
        lowest_memory = min(successful_results, key=lambda x: x.get("memory_peak_mb", float('inf')))
        highest_memory = max(successful_results, key=lambda x: x.get("memory_peak_mb", 0))
        
        # Throughput comparison
        highest_throughput = max(successful_results, key=lambda x: x.get("throughput_files_per_second", 0))
        
        summary = {
            "fastest_implementation": fastest["implementation"],
            "fastest_time_seconds": fastest["execution_time_seconds"],
            "slowest_implementation": slowest["implementation"],
            "slowest_time_seconds": slowest["execution_time_seconds"],
            "speedup_factor": slowest["execution_time_seconds"] / fastest["execution_time_seconds"] if fastest["execution_time_seconds"] > 0 else 0,
            "lowest_memory_implementation": lowest_memory["implementation"],
            "lowest_memory_mb": lowest_memory["memory_peak_mb"],
            "highest_memory_implementation": highest_memory["implementation"],
            "highest_memory_mb": highest_memory["memory_peak_mb"],
            "highest_throughput_implementation": highest_throughput["implementation"],
            "highest_throughput_files_per_second": highest_throughput["throughput_files_per_second"],
            "total_benchmarks": len(benchmark_results),
            "successful_benchmarks": len(successful_results)
        }
        
        return summary
    
    def _print_summary(self):
        """Print benchmark summary to console"""
        if not self.results or "summary" not in self.results:
            return
        
        summary = self.results["summary"]
        
        print("\n" + "=" * 80)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 80)
        
        if "error" in summary:
            print(f"❌ {summary['error']}")
            return
        
        print(f"🏆 Fastest: {summary['fastest_implementation']} ({summary['fastest_time_seconds']:.2f}s)")
        print(f"🐌 Slowest: {summary['slowest_implementation']} ({summary['slowest_time_seconds']:.2f}s)")
        print(f"⚡ Speedup: {summary['speedup_factor']:.2f}x")
        print(f"💾 Lowest Memory: {summary['lowest_memory_implementation']} ({summary['lowest_memory_mb']:.1f}MB)")
        print(f"💾 Highest Memory: {summary['highest_memory_implementation']} ({summary['highest_memory_mb']:.1f}MB)")
        print(f"🚀 Highest Throughput: {summary['highest_throughput_implementation']} ({summary['highest_throughput_files_per_second']:.2f} files/sec)")
        print(f"📈 Success Rate: {summary['successful_benchmarks']}/{summary['total_benchmarks']}")
        
        # Performance recommendations
        print("\n💡 PERFORMANCE RECOMMENDATIONS:")
        if summary['speedup_factor'] > 2:
            print(f"  • The optimized version is {summary['speedup_factor']:.1f}x faster - significant improvement!")
        elif summary['speedup_factor'] > 1.5:
            print(f"  • The optimized version is {summary['speedup_factor']:.1f}x faster - good improvement")
        else:
            print("  • Performance improvement is minimal - check configuration")
        
        if summary['lowest_memory_implementation'].startswith("optimized"):
            print("  • Optimized version uses less memory - good for large datasets")
        
        if summary['highest_throughput_implementation'].startswith("optimized"):
            print("  • Optimized version has highest throughput - best for batch processing")
    
    def _save_results(self):
        """Save benchmark results to JSON file"""
        try:
            with open(self.output_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {self.output_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save results: {e}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark PDF processing performance")
    parser.add_argument("test_folder", help="Folder containing PDF files to test")
    parser.add_argument("--tesseract", help="Path to Tesseract executable")
    parser.add_argument("--workers", nargs="+", type=int, default=[1, 2, 4, 8], 
                       help="Worker counts to test for optimized version")
    parser.add_argument("--output", default="benchmark_results.json", help="Output file for results")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.test_folder):
        print(f"Error: Test folder {args.test_folder} does not exist")
        return
    
    if not os.path.isdir(args.test_folder):
        print(f"Error: {args.test_folder} is not a directory")
        return
    
    # Run benchmark
    benchmark = PerformanceBenchmark(args.test_folder, args.output)
    results = benchmark.run_comprehensive_benchmark(args.tesseract, args.workers)
    
    print(f"\n🎯 Benchmark completed! Check {args.output} for detailed results.")


if __name__ == "__main__":
    # Example usage without command line arguments
    # Uncomment and modify the line below to run directly
    
    # benchmark = PerformanceBenchmark("SampleData")
    # results = benchmark.run_comprehensive_benchmark(
    #     tesseract_path=r"C:\Users\mmumbaiwala\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    #     worker_configs=[1, 2, 4]
    # )
    
    # Or run with command line arguments
    main()
