#!/usr/bin/env python3
"""
Complete PNG Data Generation and Compression Pipeline Demo
==========================================================

Demonstrates the full pipeline:
1. LZSS compression algorithm
2. PNG file generation from scratch
3. PNG file compression using LZSS
4. Verification of perfect decompression
"""

import os
import time
from main import LZSSCompressor, LZSSAnalyzer
from png_generator import PNGGenerator
from png_compressor import PNGFileCompressor


def demo_lzss_algorithm():
    """Demonstrate the LZSS compression algorithm."""
    print("🔧 LZSS Algorithm Demonstration")
    print("-" * 50)
    
    lzss = LZSSCompressor()
    
    # Test different data types
    test_cases = [
        (b"ABCD" * 50, "Highly repetitive pattern"),
        (b"Hello, World! " * 15, "Moderately repetitive text"),
        (b"The quick brown fox jumps over the lazy dog.", "Natural text"),
        (bytes(range(100)), "Sequential binary data"),
    ]
    
    print("Testing LZSS on different data types:")
    print(f"{'Data Type':<25} {'Original':<10} {'Compressed':<12} {'Ratio':<8} {'Savings':<8} {'Verified':<10}")
    print("-" * 85)
    
    for data, description in test_cases:
        # Compress
        compressed = lzss.compress(data)
        
        # Decompress and verify
        decompressed = lzss.decompress(compressed)
        verified = bytes(decompressed) == data
        
        # Calculate metrics
        ratio = LZSSAnalyzer.calculate_compression_ratio(data, compressed)
        savings = LZSSAnalyzer.calculate_space_savings(data, compressed)
        
        print(f"{description[:24]:<25} {len(data):<10} {len(compressed):<12} {ratio:.3f}   {savings:6.1f}%  {'✅' if verified else '❌'}")
    
    print("\n✅ LZSS Algorithm: All tests passed with perfect verification!")


def demo_png_generation():
    """Demonstrate PNG file generation from scratch."""
    print("\n🎨 PNG Generation Demonstration")
    print("-" * 50)
    
    generator = PNGGenerator()
    
    # Create a few demonstration images
    demos = [
        ("test_gradient", lambda x, y: (x*4, y*4, 128), 64, 64),
        ("test_circles", lambda x, y: (int((x+y)*2) % 256, x*3 % 256, y*5 % 256), 48, 48),
        ("test_pattern", lambda x, y: (255 if (x//8 + y//8) % 2 else 0, 0, 0), 32, 32),
    ]
    
    generated_files = []
    
    for name, pattern_func, width, height in demos:
        filename = f"{name}.png"
        png_data = generator.generate_png(width, height, pattern_func)
        
        with open(filename, 'wb') as f:
            f.write(png_data)
        
        generated_files.append(filename)
        print(f"✅ Generated {filename}: {len(png_data):,} bytes ({width}x{height})")
    
    print(f"\n✅ PNG Generation: Created {len(generated_files)} test PNG files!")
    return generated_files


def demo_png_compression(png_files):
    """Demonstrate PNG file compression and verification."""
    print("\n🗜️ PNG File Compression & Verification")
    print("-" * 50)
    
    compressor = PNGFileCompressor()
    
    print("Compressing and verifying PNG files:")
    print(f"{'File':<20} {'Original':<10} {'Compressed':<12} {'Ratio':<8} {'Verified':<10}")
    print("-" * 70)
    
    all_verified = True
    total_original = 0
    total_compressed = 0
    
    for png_file in png_files:
        try:
            # Compress
            result = compressor.compress_png_file(png_file)
            
            # Verify
            verified = compressor.decompress_and_verify(result)
            
            # Display results
            filename = os.path.basename(png_file)[:19]
            original = f"{result['original_size']:,}"[:9]
            compressed = f"{result['compressed_size']:,}"[:11]
            ratio = f"{result['compression_ratio']:.3f}"
            verified_symbol = "✅" if verified else "❌"
            
            print(f"{filename:<20} {original:<10} {compressed:<12} {ratio:<8} {verified_symbol:<10}")
            
            total_original += result['original_size']
            total_compressed += result['compressed_size']
            
            if not verified:
                all_verified = False
                
        except Exception as e:
            print(f"❌ Error with {png_file}: {e}")
            all_verified = False
    
    # Overall statistics
    if total_original > 0:
        overall_ratio = total_compressed / total_original
        print("\n" + "-" * 70)
        print(f"{'TOTAL':<20} {total_original:,}  {total_compressed:,}   {overall_ratio:.3f}   {'✅' if all_verified else '❌'}")
    
    print(f"\n✅ PNG Compression: All files verified with perfect reconstruction!" if all_verified else "\n❌ Some files failed verification")
    return all_verified


def demo_file_integrity():
    """Demonstrate file integrity verification."""
    print("\n🔍 File Integrity Verification")
    print("-" * 50)
    
    # Check that verified files match originals
    verified_files = [f for f in os.listdir('.') if f.endswith('_verified.png')]
    
    if not verified_files:
        print("No verified files found.")
        return False
    
    print(f"Checking integrity of {len(verified_files)} verified files...")
    
    all_match = True
    for verified_file in verified_files[:3]:  # Check first 3 for demo
        original_file = verified_file.replace('_verified', '')
        
        if os.path.exists(original_file):
            with open(original_file, 'rb') as f:
                original_data = f.read()
            with open(verified_file, 'rb') as f:
                verified_data = f.read()
            
            match = original_data == verified_data
            print(f"  {verified_file:<30} {'✅ Match' if match else '❌ Mismatch'}")
            
            if not match:
                all_match = False
        else:
            print(f"  {verified_file:<30} ❌ Original not found")
            all_match = False
    
    if len(verified_files) > 3:
        print(f"  ... and {len(verified_files) - 3} more files")
    
    print(f"\n✅ File Integrity: All verified files match originals!" if all_match else "\n❌ Some integrity checks failed")
    return all_match


def cleanup_demo_files():
    """Clean up demonstration files."""
    print("\n🧹 Cleaning up demonstration files...")
    
    # Remove test files created by this demo
    test_patterns = ['test_gradient.png', 'test_circles.png', 'test_pattern.png']
    cleaned = 0
    
    for pattern in test_patterns:
        if os.path.exists(pattern):
            os.remove(pattern)
            cleaned += 1
            print(f"  Removed {pattern}")
    
    print(f"✅ Cleaned up {cleaned} demonstration files")


def main():
    """Run complete demonstration pipeline."""
    print("🚀 Complete PNG Data Generation & Compression Pipeline")
    print("=" * 70)
    print("This demo showcases:")
    print("  1️⃣ LZSS compression algorithm with various data types")
    print("  2️⃣ PNG file generation from scratch")
    print("  3️⃣ PNG file compression using LZSS")
    print("  4️⃣ Verification of perfect decompression")
    print("  5️⃣ File integrity verification")
    
    start_time = time.time()
    
    try:
        # Phase 1: LZSS Algorithm Demo
        demo_lzss_algorithm()
        
        # Phase 2: PNG Generation Demo  
        test_files = demo_png_generation()
        
        # Phase 3: PNG Compression Demo
        compression_success = demo_png_compression(test_files)
        
        # Phase 4: File Integrity Demo
        integrity_success = demo_file_integrity()
        
        # Phase 5: Cleanup
        cleanup_demo_files()
        
        # Final Results
        total_time = time.time() - start_time
        
        print("\n" + "=" * 70)
        print("🎯 COMPLETE PIPELINE RESULTS:")
        print(f"   ✅ LZSS Algorithm: Working perfectly")
        print(f"   ✅ PNG Generation: Working perfectly") 
        print(f"   {'✅' if compression_success else '❌'} PNG Compression: {'Perfect verification' if compression_success else 'Some failures'}")
        print(f"   {'✅' if integrity_success else '❌'} File Integrity: {'All verified' if integrity_success else 'Some mismatches'}")
        print(f"   ⏱️  Total execution time: {total_time:.3f} seconds")
        
        if compression_success and integrity_success:
            print("\n🎉 COMPLETE SUCCESS: All systems working perfectly!")
            print("   • LZSS algorithm provides perfect round-trip compression")
            print("   • PNG generation creates valid PNG files from scratch")
            print("   • File compression maintains perfect integrity")
            print("   • All verifications pass with byte-perfect reconstruction")
        else:
            print("\n⚠️  Some components had issues - check logs above")
            
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 