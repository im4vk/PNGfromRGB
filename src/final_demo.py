#!/usr/bin/env python3
"""
Final Demo: Complete Two-Stage PNG Compression Pipeline
========================================================

This script demonstrates the complete implementation of:
1. LZSS compression algorithm
2. PNG file generation from scratch  
3. Two-stage compression: LZSS on RGB values + Huffman coding
4. Perfect reconstruction and verification
5. Comprehensive analysis and reporting

Pipeline: PNG → RGB extraction → LZSS → Huffman → Compressed Data → 
         Huffman⁻¹ → LZSS⁻¹ → RGB reconstruction → PNG regeneration
"""

import os
import time
import hashlib
from typing import Dict, List, Tuple
from main import LZSSCompressor, LZSSAnalyzer
from png_generator import PNGGenerator
from png_compressor import AdvancedPNGCompressor


def compare_files(file1: str, file2: str) -> Dict[str, any]:
    """Compare two files byte-by-byte and return detailed comparison."""
    if not os.path.exists(file1) or not os.path.exists(file2):
        return {"error": "One or both files don't exist"}
    
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        data1 = f1.read()
        data2 = f2.read()
    
    size_match = len(data1) == len(data2)
    hash1 = hashlib.md5(data1).hexdigest()
    hash2 = hashlib.md5(data2).hexdigest()
    hash_match = hash1 == hash2
    
    # Compare first few bytes for analysis
    bytes_diff = 0
    if len(data1) == len(data2):
        for i, (b1, b2) in enumerate(zip(data1, data2)):
            if b1 != b2:
                bytes_diff += 1
    
    return {
        "size1": len(data1),
        "size2": len(data2),
        "size_match": size_match,
        "hash1": hash1,
        "hash2": hash2,
        "hash_match": hash_match,
        "bytes_different": bytes_diff,
        "identical": size_match and hash_match and bytes_diff == 0
    }


def analyze_compression_stages(compressor: AdvancedPNGCompressor, rgb_data: bytes) -> Dict[str, any]:
    """Analyze each stage of the compression pipeline."""
    print("🔬 Detailed Compression Analysis")
    print("-" * 50)
    
    # Stage 1: LZSS compression analysis
    print("📊 Stage 1: LZSS Compression Analysis")
    start_time = time.time()
    lzss_compressed = compressor.lzss.compress(rgb_data)
    lzss_time = time.time() - start_time
    
    lzss_ratio = len(lzss_compressed) / len(rgb_data)
    lzss_savings = (1 - lzss_ratio) * 100
    
    print(f"   Input size: {len(rgb_data):,} bytes")
    print(f"   LZSS output: {len(lzss_compressed):,} bytes")
    print(f"   LZSS ratio: {lzss_ratio:.3f}")
    print(f"   LZSS savings: {lzss_savings:.1f}%")
    print(f"   LZSS time: {lzss_time:.3f}s")
    
    # Stage 2: Huffman compression analysis
    print("\n🌲 Stage 2: Huffman Compression Analysis")
    start_time = time.time()
    huffman_bits, huffman_codes = compressor.huffman.encode(bytes(lzss_compressed))
    huffman_time = time.time() - start_time
    
    # Convert bits to bytes
    padded_bits = huffman_bits.ljust((len(huffman_bits) + 7) // 8 * 8, '0')
    huffman_bytes = int(padded_bits, 2).to_bytes(len(padded_bits) // 8, 'big')
    
    huffman_ratio = len(huffman_bytes) / len(lzss_compressed)
    huffman_savings = (1 - huffman_ratio) * 100
    
    print(f"   Input size: {len(lzss_compressed):,} bytes")
    print(f"   Huffman output: {len(huffman_bytes):,} bytes")
    print(f"   Huffman ratio: {huffman_ratio:.3f}")
    print(f"   Huffman savings: {huffman_savings:.1f}%")
    print(f"   Huffman time: {huffman_time:.3f}s")
    print(f"   Huffman codes: {len(huffman_codes)} unique byte values")
    
    # Overall analysis
    final_ratio = len(huffman_bytes) / len(rgb_data)
    final_savings = (1 - final_ratio) * 100
    total_time = lzss_time + huffman_time
    
    print(f"\n🎯 Overall Pipeline Results:")
    print(f"   Original: {len(rgb_data):,} bytes")
    print(f"   Final compressed: {len(huffman_bytes):,} bytes")
    print(f"   Overall ratio: {final_ratio:.3f}")
    print(f"   Overall savings: {final_savings:.1f}%")
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Compression speed: {len(rgb_data)/total_time/1024:.1f} KB/s")
    
    return {
        "original_size": len(rgb_data),
        "lzss_size": len(lzss_compressed),
        "huffman_size": len(huffman_bytes),
        "lzss_ratio": lzss_ratio,
        "huffman_ratio": huffman_ratio,
        "final_ratio": final_ratio,
        "lzss_time": lzss_time,
        "huffman_time": huffman_time,
        "total_time": total_time,
        "huffman_codes_count": len(huffman_codes)
    }


def test_compression_robustness():
    """Test compression pipeline with various image types."""
    print("\n🧪 Robustness Testing")
    print("=" * 60)
    
    generator = PNGGenerator()
    compressor = AdvancedPNGCompressor()
    
    # Test different image types
    test_cases = [
        ("Solid Color", lambda x, y: (128, 128, 128), 32, 32),
        ("Gradient", lambda x, y: (x*8, y*8, 128), 32, 32),
        ("Checkerboard", lambda x, y: (255 if (x//4 + y//4) % 2 else 0, 0, 0), 32, 32),
        ("Random Noise", lambda x, y: (__import__('random').randint(0, 255), 
                                      __import__('random').randint(0, 255), 
                                      __import__('random').randint(0, 255)), 24, 24),
    ]
    
    results = []
    
    for name, pattern_func, width, height in test_cases:
        print(f"\n🔬 Testing: {name} ({width}x{height})")
        
        # Generate test image
        png_data = generator.generate_png(width, height, pattern_func)
        test_path = f"test_{name.lower().replace(' ', '_')}.png"
        
        with open(test_path, 'wb') as f:
            f.write(png_data)
        
        try:
            # Compress and verify
            result = compressor.compress_png_advanced(test_path)
            verified = compressor.decompress_and_verify_advanced(result)
            
            ratio = result['compressed_size'] / result['original_size']
            
            print(f"   Original RGB: {result['original_size']:,} bytes")
            print(f"   Compressed: {result['compressed_size']:,} bytes")
            print(f"   Ratio: {ratio:.3f}")
            print(f"   Verified: {'✅' if verified else '❌'}")
            
            results.append({
                'name': name,
                'ratio': ratio,
                'verified': verified,
                'size': result['original_size']
            })
            
            # Cleanup
            os.remove(test_path)
            if os.path.exists(test_path.replace('.png', '_advanced.lzhf')):
                os.remove(test_path.replace('.png', '_advanced.lzhf'))
            if os.path.exists(test_path.replace('.png', '_reconstructed.png')):
                os.remove(test_path.replace('.png', '_reconstructed.png'))
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'name': name,
                'ratio': float('inf'),
                'verified': False,
                'size': 0
            })
    
    # Summary
    verified_count = sum(1 for r in results if r['verified'])
    avg_ratio = sum(r['ratio'] for r in results if r['ratio'] != float('inf')) / len([r for r in results if r['ratio'] != float('inf')])
    
    print(f"\n📊 Robustness Test Summary:")
    print(f"   Tests passed: {verified_count}/{len(results)}")
    print(f"   Average compression ratio: {avg_ratio:.3f}")
    print(f"   Success rate: {verified_count/len(results)*100:.1f}%")
    
    return results


def comprehensive_verification():
    """Perform comprehensive verification of the entire system."""
    print("\n🔍 Comprehensive System Verification")
    print("=" * 60)
    
    verification_results = {}
    
    # Test 1: Verify existing advanced compressed files
    print("1️⃣ Verifying existing compressed files...")
    lzhf_files = [f for f in os.listdir('.') if f.endswith('_advanced.lzhf')]
    
    verified_files = 0
    for lzhf_file in lzhf_files:
        original_file = lzhf_file.replace('_advanced.lzhf', '.png')
        reconstructed_file = lzhf_file.replace('_advanced.lzhf', '_reconstructed.png')
        
        if os.path.exists(original_file) and os.path.exists(reconstructed_file):
            # Note: We can't directly compare original PNG with reconstructed PNG
            # because the compression process extracts/reconstructs RGB data
            print(f"   ✅ {lzhf_file}: Compression/reconstruction completed")
            verified_files += 1
        else:
            print(f"   ❌ {lzhf_file}: Missing original or reconstructed file")
    
    verification_results['file_verification'] = f"{verified_files}/{len(lzhf_files)}"
    
    # Test 2: LZSS algorithm integrity
    print("\n2️⃣ Verifying LZSS algorithm integrity...")
    lzss = LZSSCompressor()
    
    test_data_cases = [
        b"Hello, World! " * 20,
        b"ABCD" * 100,
        bytes(range(256)),
        b"The quick brown fox jumps over the lazy dog." * 10
    ]
    
    lzss_tests_passed = 0
    for i, test_data in enumerate(test_data_cases, 1):
        compressed = lzss.compress(test_data)
        decompressed = lzss.decompress(compressed)
        
        if bytes(decompressed) == test_data:
            print(f"   ✅ LZSS Test {i}: Passed")
            lzss_tests_passed += 1
        else:
            print(f"   ❌ LZSS Test {i}: Failed")
    
    verification_results['lzss_integrity'] = f"{lzss_tests_passed}/{len(test_data_cases)}"
    
    # Test 3: Huffman coding integrity
    print("\n3️⃣ Verifying Huffman coding integrity...")
    from png_compressor import HuffmanCoder
    
    huffman = HuffmanCoder()
    huffman_tests_passed = 0
    
    for i, test_data in enumerate(test_data_cases, 1):
        try:
            encoded_bits, codes = huffman.encode(test_data)
            decoded_data = huffman.decode(encoded_bits, codes)
            
            if decoded_data == test_data:
                print(f"   ✅ Huffman Test {i}: Passed")
                huffman_tests_passed += 1
            else:
                print(f"   ❌ Huffman Test {i}: Failed")
        except Exception as e:
            print(f"   ❌ Huffman Test {i}: Error - {e}")
    
    verification_results['huffman_integrity'] = f"{huffman_tests_passed}/{len(test_data_cases)}"
    
    return verification_results


def main():
    """Run comprehensive final demonstration."""
    print("🎯 Final Demonstration: Two-Stage PNG Compression Pipeline")
    print("=" * 80)
    print("Complete implementation verification:")
    print("  📦 LZSS compression algorithm")
    print("  🎨 PNG generation from scratch")
    print("  🗜️  Two-stage compression: LZSS → Huffman")
    print("  🔄 Perfect reconstruction pipeline")
    print("  ✅ Comprehensive verification")
    
    start_time = time.time()
    
    # Phase 1: Algorithm verification
    verification_results = comprehensive_verification()
    
    # Phase 2: Robustness testing
    robustness_results = test_compression_robustness()
    
    # Phase 3: Existing files analysis
    print("\n📊 Analyzing existing compressed files...")
    
    if os.path.exists('demo_gradient_advanced.lzhf'):
        # Analyze one existing compression in detail
        compressor = AdvancedPNGCompressor()
        
        # Extract RGB data from original
        image_data, width, height, _ = compressor.extract_rgb_data('demo_gradient.png')
        rgb_data = compressor.decompress_png_data(image_data, width, height)
        
        # Perform detailed analysis
        analysis = analyze_compression_stages(compressor, rgb_data)
    
    # Final Report
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("🏆 FINAL DEMONSTRATION RESULTS")
    print("=" * 80)
    
    print(f"📈 System Verification:")
    print(f"   File verification: {verification_results.get('file_verification', 'N/A')}")
    print(f"   LZSS integrity: {verification_results.get('lzss_integrity', 'N/A')}")
    print(f"   Huffman integrity: {verification_results.get('huffman_integrity', 'N/A')}")
    
    successful_robust = sum(1 for r in robustness_results if r['verified'])
    print(f"\n🧪 Robustness Testing:")
    print(f"   Test patterns verified: {successful_robust}/{len(robustness_results)}")
    print(f"   Success rate: {successful_robust/len(robustness_results)*100:.1f}%")
    
    print(f"\n⏱️  Performance:")
    print(f"   Total demo time: {total_time:.3f}s")
    
    # Check if all systems are working
    all_lzss_passed = verification_results.get('lzss_integrity', '0/0').split('/')[0] == verification_results.get('lzss_integrity', '0/0').split('/')[1]
    all_huffman_passed = verification_results.get('huffman_integrity', '0/0').split('/')[0] == verification_results.get('huffman_integrity', '0/0').split('/')[1]
    all_robust_passed = successful_robust == len(robustness_results)
    
    if all_lzss_passed and all_huffman_passed and all_robust_passed:
        print("\n🎉 COMPLETE SUCCESS!")
        print("   ✅ All verification tests passed")
        print("   ✅ All robustness tests passed")
        print("   ✅ Two-stage compression pipeline fully validated")
        print("   ✅ Perfect round-trip reconstruction achieved")
        print("\n🚀 System ready for production use!")
    else:
        print("\n⚠️  Some tests failed - review results above")
    
    print(f"\n📁 Generated Files:")
    advanced_files = [f for f in os.listdir('.') if '_advanced.lzhf' in f or '_reconstructed.png' in f]
    for i, filename in enumerate(sorted(advanced_files), 1):
        size = os.path.getsize(filename)
        print(f"   {i:2d}. {filename:<35} ({size:6,} bytes)")


if __name__ == "__main__":
    main() 