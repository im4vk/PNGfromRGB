#!/usr/bin/env python3
"""
Advanced PNG Image Compression with LZSS + Huffman Coding
==========================================================

This module implements a sophisticated two-stage compression pipeline:
1. Apply LZSS compression to RGB pixel values
2. Apply Huffman coding to the LZSS output
3. Save as compressed image data with metadata
4. Perfect reconstruction by reversing the process

Pipeline: RGB pixels → LZSS → Huffman → Compressed Data → Huffman⁻¹ → LZSS⁻¹ → RGB pixels
"""

import os
import time
import struct
import hashlib
import heapq
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional, Any
from main import LZSSCompressor, LZSSAnalyzer
from png_generator import PNGGenerator


class HuffmanNode:
    """Node for Huffman tree construction."""
    
    def __init__(self, char: Optional[int] = None, freq: int = 0, 
                 left: 'HuffmanNode' = None, right: 'HuffmanNode' = None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right
    
    def __lt__(self, other):
        return self.freq < other.freq


class HuffmanCoder:
    """Huffman coding implementation for compression."""
    
    def __init__(self):
        self.codes: Dict[int, str] = {}
        self.reverse_codes: Dict[str, int] = {}
        self.tree: Optional[HuffmanNode] = None
    
    def build_frequency_table(self, data: bytes) -> Dict[int, int]:
        """Build frequency table for bytes in data."""
        return Counter(data)
    
    def build_huffman_tree(self, frequencies: Dict[int, int]) -> HuffmanNode:
        """Build Huffman tree from frequency table."""
        if not frequencies:
            return None
        
        # Create heap of nodes
        heap = []
        for char, freq in frequencies.items():
            heapq.heappush(heap, HuffmanNode(char, freq))
        
        # Handle single character case
        if len(heap) == 1:
            root = HuffmanNode(freq=heap[0].freq)
            root.left = heapq.heappop(heap)
            return root
        
        # Build tree
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            
            merged = HuffmanNode(freq=left.freq + right.freq)
            merged.left = left
            merged.right = right
            
            heapq.heappush(heap, merged)
        
        return heap[0]
    
    def generate_codes(self, root: HuffmanNode, code: str = "", codes: Dict[int, str] = None) -> Dict[int, str]:
        """Generate Huffman codes from tree."""
        if codes is None:
            codes = {}
        
        if root is None:
            return codes
        
        # Leaf node
        if root.char is not None:
            codes[root.char] = code if code else "0"  # Single char case
            return codes
        
        # Traverse tree
        self.generate_codes(root.left, code + "0", codes)
        self.generate_codes(root.right, code + "1", codes)
        
        return codes
    
    def build_codes(self, data: bytes) -> None:
        """Build Huffman codes for given data."""
        frequencies = self.build_frequency_table(data)
        self.tree = self.build_huffman_tree(frequencies)
        self.codes = self.generate_codes(self.tree)
        self.reverse_codes = {v: k for k, v in self.codes.items()}
    
    def encode(self, data: bytes) -> Tuple[str, Dict[int, str]]:
        """Encode data using Huffman coding."""
        if not data:
            return "", {}
        
        self.build_codes(data)
        
        encoded = ""
        for byte in data:
            encoded += self.codes[byte]
        
        return encoded, self.codes
    
    def decode(self, encoded_bits: str, codes: Dict[int, str]) -> bytes:
        """Decode Huffman encoded data."""
        if not encoded_bits or not codes:
            return b""
        
        # Build reverse mapping
        reverse_codes = {v: k for k, v in codes.items()}
        
        decoded = bytearray()
        current_code = ""
        
        for bit in encoded_bits:
            current_code += bit
            if current_code in reverse_codes:
                decoded.append(reverse_codes[current_code])
                current_code = ""
        
        return bytes(decoded)
    
    def serialize_codes(self, codes: Dict[int, str]) -> bytes:
        """Serialize Huffman codes for storage."""
        # Format: num_codes (2 bytes) + [byte (1) + code_length (1) + code_bits (variable)]
        serialized = struct.pack('>H', len(codes))
        
        for byte_val, code in codes.items():
            code_length = len(code)
            # Convert code string to bytes (pad to byte boundary)
            code_bits = code.ljust((code_length + 7) // 8 * 8, '0')
            code_bytes = int(code_bits, 2).to_bytes(len(code_bits) // 8, 'big')
            
            serialized += struct.pack('>BB', byte_val, code_length)
            serialized += code_bytes
        
        return serialized
    
    def deserialize_codes(self, data: bytes, offset: int = 0) -> Tuple[Dict[int, str], int]:
        """Deserialize Huffman codes from storage."""
        codes = {}
        
        num_codes = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
        
        for _ in range(num_codes):
            byte_val, code_length = struct.unpack('>BB', data[offset:offset+2])
            offset += 2
            
            # Read code bits
            code_bytes_needed = (code_length + 7) // 8
            code_bytes = data[offset:offset+code_bytes_needed]
            offset += code_bytes_needed
            
            # Convert bytes back to code string
            code_int = int.from_bytes(code_bytes, 'big')
            code_bits = format(code_int, f'0{code_bytes_needed * 8}b')
            code = code_bits[:code_length]  # Trim padding
            
            codes[byte_val] = code
        
        return codes, offset


class AdvancedPNGCompressor:
    """Advanced PNG compressor with LZSS + Huffman coding."""
    
    def __init__(self):
        """Initialize advanced PNG compressor."""
        self.lzss = LZSSCompressor()
        self.huffman = HuffmanCoder()
        self.compression_results: List[Dict] = []
    
    def extract_rgb_data(self, png_path: str) -> Tuple[bytes, int, int, bytes]:
        """Extract RGB pixel data from PNG file."""
        with open(png_path, 'rb') as f:
            png_data = f.read()
        
        # Parse PNG to extract image data
        pos = 8  # Skip PNG signature
        width = height = 0
        image_data = b""
        
        while pos < len(png_data):
            if pos + 8 > len(png_data):
                break
                
            length = struct.unpack('>I', png_data[pos:pos+4])[0]
            chunk_type = png_data[pos+4:pos+8]
            
            if chunk_type == b'IHDR':
                width, height = struct.unpack('>II', png_data[pos+8:pos+16])
            elif chunk_type == b'IDAT':
                image_data += png_data[pos+8:pos+8+length]
            
            pos += 8 + length + 4  # Skip header + data + CRC
            
            if chunk_type == b'IEND':
                break
        
        return image_data, width, height, png_data
    
    def decompress_png_data(self, compressed_data: bytes, width: int, height: int) -> bytes:
        """Decompress PNG IDAT data to get raw RGB pixels."""
        import zlib
        
        # Decompress PNG data
        raw_data = zlib.decompress(compressed_data)
        
        # Remove filter bytes (assuming filter type 0 for simplicity)
        rgb_data = bytearray()
        bytes_per_row = width * 3  # RGB
        
        for y in range(height):
            row_start = y * (bytes_per_row + 1)  # +1 for filter byte
            row_data = raw_data[row_start + 1:row_start + 1 + bytes_per_row]  # Skip filter byte
            rgb_data.extend(row_data)
        
        return bytes(rgb_data)
    
    def compress_rgb_data(self, rgb_data: bytes, width: int, height: int) -> bytes:
        """Compress RGB data back to PNG format."""
        import zlib
        
        # Add filter bytes (type 0 = no filter)
        filtered_data = bytearray()
        bytes_per_row = width * 3
        
        for y in range(height):
            filtered_data.append(0)  # Filter type 0
            row_start = y * bytes_per_row
            filtered_data.extend(rgb_data[row_start:row_start + bytes_per_row])
        
        # Compress with zlib
        return zlib.compress(bytes(filtered_data))
    
    def two_stage_compress(self, rgb_data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """Apply two-stage compression: LZSS + Huffman."""
        print(f"📊 Starting two-stage compression on {len(rgb_data)} RGB bytes...")
        
        # Stage 1: LZSS compression
        print("   🔧 Stage 1: LZSS compression...")
        start_time = time.time()
        lzss_compressed = self.lzss.compress(rgb_data)
        lzss_time = time.time() - start_time
        
        lzss_ratio = len(lzss_compressed) / len(rgb_data)
        print(f"      LZSS: {len(rgb_data)} → {len(lzss_compressed)} bytes ({lzss_ratio:.3f} ratio)")
        print(f"      LZSS time: {lzss_time:.3f}s")
        
        # Stage 2: Huffman coding
        print("   🌲 Stage 2: Huffman coding...")
        start_time = time.time()
        huffman_bits, huffman_codes = self.huffman.encode(bytes(lzss_compressed))
        huffman_time = time.time() - start_time
        
        # Convert bits to bytes (pad to byte boundary)
        padded_bits = huffman_bits.ljust((len(huffman_bits) + 7) // 8 * 8, '0')
        huffman_bytes = int(padded_bits, 2).to_bytes(len(padded_bits) // 8, 'big')
        
        # Serialize the complete compressed data
        metadata = {
            'original_size': len(rgb_data),
            'lzss_size': len(lzss_compressed),
            'huffman_bits': len(huffman_bits),
            'huffman_codes': huffman_codes,
            'lzss_time': lzss_time,
            'huffman_time': huffman_time
        }
        
        # Create final compressed data with metadata
        compressed_data = self.serialize_compressed_data(huffman_bytes, len(huffman_bits), huffman_codes)
        
        final_ratio = len(compressed_data) / len(rgb_data)
        total_time = lzss_time + huffman_time
        
        print(f"      Huffman: {len(lzss_compressed)} → {len(huffman_bytes)} bytes")
        print(f"      Huffman time: {huffman_time:.3f}s")
        print(f"   🎯 Final: {len(rgb_data)} → {len(compressed_data)} bytes ({final_ratio:.3f} ratio)")
        print(f"   ⏱️  Total time: {total_time:.3f}s")
        
        metadata['final_size'] = len(compressed_data)
        metadata['final_ratio'] = final_ratio
        metadata['total_time'] = total_time
        
        return compressed_data, metadata
    
    def two_stage_decompress(self, compressed_data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """Decompress two-stage compressed data: Huffman⁻¹ + LZSS⁻¹."""
        print(f"🔄 Starting two-stage decompression on {len(compressed_data)} bytes...")
        
        # Deserialize compressed data
        huffman_bytes, huffman_bits_length, huffman_codes, offset = self.deserialize_compressed_data(compressed_data)
        
        # Stage 1: Huffman decoding
        print("   🌲 Stage 1: Huffman decoding...")
        start_time = time.time()
        
        # Convert bytes back to bits
        huffman_bits_padded = ''.join(format(b, '08b') for b in huffman_bytes)
        huffman_bits = huffman_bits_padded[:huffman_bits_length]  # Remove padding
        
        lzss_data = self.huffman.decode(huffman_bits, huffman_codes)
        huffman_time = time.time() - start_time
        
        print(f"      Huffman decode: {len(huffman_bytes)} → {len(lzss_data)} bytes")
        print(f"      Huffman decode time: {huffman_time:.3f}s")
        
        # Stage 2: LZSS decompression
        print("   🔧 Stage 2: LZSS decompression...")
        start_time = time.time()
        rgb_data = self.lzss.decompress(bytearray(lzss_data))
        lzss_time = time.time() - start_time
        
        print(f"      LZSS decompress: {len(lzss_data)} → {len(rgb_data)} bytes")
        print(f"      LZSS decompress time: {lzss_time:.3f}s")
        
        total_time = huffman_time + lzss_time
        print(f"   🎯 Final: {len(compressed_data)} → {len(rgb_data)} bytes")
        print(f"   ⏱️  Total time: {total_time:.3f}s")
        
        metadata = {
            'huffman_decode_time': huffman_time,
            'lzss_decode_time': lzss_time,
            'total_decode_time': total_time
        }
        
        return bytes(rgb_data), metadata
    
    def serialize_compressed_data(self, huffman_bytes: bytes, huffman_bits_length: int, 
                                 huffman_codes: Dict[int, str]) -> bytes:
        """Serialize compressed data with metadata."""
        # Format: magic(4) + huffman_bits_length(4) + codes_data + huffman_bytes
        magic = b'LZHF'  # LZSS + Huffman magic
        
        serialized = magic
        serialized += struct.pack('>I', huffman_bits_length)
        
        # Serialize Huffman codes
        codes_data = self.huffman.serialize_codes(huffman_codes)
        serialized += struct.pack('>I', len(codes_data))
        serialized += codes_data
        
        # Add Huffman compressed data
        serialized += huffman_bytes
        
        return serialized
    
    def deserialize_compressed_data(self, compressed_data: bytes) -> Tuple[bytes, int, Dict[int, str], int]:
        """Deserialize compressed data with metadata."""
        offset = 0
        
        # Check magic
        magic = compressed_data[offset:offset+4]
        if magic != b'LZHF':
            raise ValueError("Invalid compressed data format")
        offset += 4
        
        # Read huffman bits length
        huffman_bits_length = struct.unpack('>I', compressed_data[offset:offset+4])[0]
        offset += 4
        
        # Read codes data length
        codes_length = struct.unpack('>I', compressed_data[offset:offset+4])[0]
        offset += 4
        
        # Deserialize Huffman codes
        huffman_codes, new_offset = self.huffman.deserialize_codes(compressed_data, offset)
        offset = new_offset
        
        # Read Huffman compressed data
        huffman_bytes = compressed_data[offset:]
        
        return huffman_bytes, huffman_bits_length, huffman_codes, offset
    
    def compress_png_advanced(self, png_path: str) -> Dict[str, Any]:
        """Compress PNG using advanced two-stage compression."""
        if not os.path.exists(png_path):
            raise FileNotFoundError(f"PNG file not found: {png_path}")
        
        print(f"🎨 Advanced PNG Compression: {png_path}")
        print("=" * 60)
        
        # Extract RGB data from PNG
        print("📖 Extracting RGB data from PNG...")
        image_data, width, height, original_png = self.extract_rgb_data(png_path)
        
        try:
            rgb_data = self.decompress_png_data(image_data, width, height)
            print(f"   Extracted {len(rgb_data)} RGB bytes ({width}x{height})")
        except Exception as e:
            print(f"   Error extracting RGB data: {e}")
            print("   Using raw image data instead...")
            rgb_data = image_data
        
        original_hash = hashlib.md5(rgb_data).hexdigest()
        
        # Apply two-stage compression
        compressed_data, compress_metadata = self.two_stage_compress(rgb_data)
        
        # Save compressed data
        compressed_path = png_path.replace('.png', '_advanced.lzhf')
        with open(compressed_path, 'wb') as f:
            f.write(compressed_data)
        
        print(f"💾 Saved compressed: {compressed_path}")
        
        result = {
            'original_path': png_path,
            'compressed_path': compressed_path,
            'width': width,
            'height': height,
            'original_size': len(rgb_data),
            'compressed_size': len(compressed_data),
            'original_hash': original_hash,
            'compression_metadata': compress_metadata
        }
        
        return result
    
    def decompress_and_verify_advanced(self, result: Dict[str, Any]) -> bool:
        """Decompress and verify advanced compressed data."""
        compressed_path = result['compressed_path']
        original_path = result['original_path']
        
        print(f"🔍 Advanced Verification: {compressed_path}")
        print("=" * 60)
        
        # Read compressed data
        with open(compressed_path, 'rb') as f:
            compressed_data = f.read()
        
        # Decompress using two-stage process
        decompressed_rgb, decompress_metadata = self.two_stage_decompress(compressed_data)
        
        # Verify integrity
        decompressed_hash = hashlib.md5(decompressed_rgb).hexdigest()
        original_hash = result['original_hash']
        
        size_match = len(decompressed_rgb) == result['original_size']
        hash_match = decompressed_hash == original_hash
        
        print(f"📊 Verification Results:")
        print(f"   Original size: {result['original_size']:,} bytes")
        print(f"   Decompressed size: {len(decompressed_rgb):,} bytes")
        print(f"   Original MD5: {original_hash}")
        print(f"   Decompressed MD5: {decompressed_hash}")
        print(f"   Size match: {'✅' if size_match else '❌'}")
        print(f"   Hash match: {'✅' if hash_match else '❌'}")
        print(f"   Byte-perfect: {'✅' if size_match and hash_match else '❌'}")
        
        # If verification successful, recreate the PNG
        if size_match and hash_match:
            print("🔄 Reconstructing PNG file...")
            try:
                # Recreate PNG file
                reconstructed_path = original_path.replace('.png', '_reconstructed.png')
                
                # For now, create a new PNG with the RGB data
                # In a full implementation, we'd need to store PNG metadata
                generator = PNGGenerator()
                width, height = result['width'], result['height']
                
                def rgb_from_data(x, y):
                    pixel_idx = (y * width + x) * 3
                    if pixel_idx + 2 < len(decompressed_rgb):
                        return (decompressed_rgb[pixel_idx], 
                               decompressed_rgb[pixel_idx + 1], 
                               decompressed_rgb[pixel_idx + 2])
                    return (0, 0, 0)
                
                reconstructed_png = generator.generate_png(width, height, rgb_from_data)
                
                with open(reconstructed_path, 'wb') as f:
                    f.write(reconstructed_png)
                
                print(f"💾 Saved reconstructed: {reconstructed_path}")
                
            except Exception as e:
                print(f"⚠️  Could not reconstruct PNG: {e}")
        
        # Update result with verification info
        result.update({
            'decompression_metadata': decompress_metadata,
            'decompressed_hash': decompressed_hash,
            'size_match': size_match,
            'hash_match': hash_match,
            'verification_success': size_match and hash_match
        })
        
        return size_match and hash_match
    
    def compress_random_image(self, image_size: Tuple[int, int] = (128, 128)) -> Dict[str, Any]:
        """Create and compress a random image for demonstration."""
        import random
        
        width, height = image_size
        print(f"🎲 Creating random image ({width}x{height})...")
        
        # Generate random RGB data
        def random_rgb(x, y):
            return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        generator = PNGGenerator()
        png_data = generator.generate_png(width, height, random_rgb)
        
        # Save random image
        random_path = "random_test_image.png"
        with open(random_path, 'wb') as f:
            f.write(png_data)
        
        print(f"💾 Created random image: {random_path} ({len(png_data)} bytes)")
        
        # Compress it
        result = self.compress_png_advanced(random_path)
        return result


def main():
    """Demonstrate advanced PNG compression with LZSS + Huffman."""
    print("🚀 Advanced PNG Compression Demo (LZSS + Huffman)")
    print("=" * 80)
    print("Pipeline: RGB pixels → LZSS → Huffman → Compressed → Huffman⁻¹ → LZSS⁻¹ → RGB")
    print()
    
    compressor = AdvancedPNGCompressor()
    
    # Test 1: Compress a random image
    print("🎲 TEST 1: Random Image Compression")
    print("-" * 50)
    
    random_result = compressor.compress_random_image((64, 64))
    random_verified = compressor.decompress_and_verify_advanced(random_result)
    
    print(f"\n✅ Random image test: {'PASSED' if random_verified else 'FAILED'}")
    
    # Test 2: Compress existing PNG files
    print("\n📁 TEST 2: Existing PNG Files")
    print("-" * 50)
    
    png_files = [f for f in os.listdir('.') if f.endswith('.png') and 'random' not in f and 'reconstructed' not in f][:3]
    
    if png_files:
        results = []
        successful = 0
        
        for png_file in png_files:
            try:
                print(f"\n🖼️  Processing: {png_file}")
                result = compressor.compress_png_advanced(png_file)
                verified = compressor.decompress_and_verify_advanced(result)
                
                if verified:
                    successful += 1
                
                results.append(result)
                print(f"   Result: {'✅ VERIFIED' if verified else '❌ FAILED'}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Summary report
        print(f"\n📊 SUMMARY REPORT")
        print("=" * 80)
        print(f"Files processed: {len(results)}")
        print(f"Successful verifications: {successful}/{len(results)}")
        print(f"Success rate: {successful/len(results)*100:.1f}%" if results else "0%")
        
        if results:
            total_original = sum(r['original_size'] for r in results)
            total_compressed = sum(r['compressed_size'] for r in results)
            overall_ratio = total_compressed / total_original if total_original > 0 else 0
            
            print(f"Overall compression ratio: {overall_ratio:.3f}")
            print(f"Overall space savings: {(1-overall_ratio)*100:.1f}%")
            
            print(f"\n📋 Per-File Results:")
            print(f"{'File':<25} {'Original':<10} {'Compressed':<12} {'Ratio':<8} {'Verified':<10}")
            print("-" * 75)
            
            for result in results:
                filename = os.path.basename(result['original_path'])[:24]
                original = f"{result['original_size']:,}"[:9]
                compressed = f"{result['compressed_size']:,}"[:11]
                ratio = f"{result['compressed_size']/result['original_size']:.3f}"
                verified = "✅" if result.get('verification_success', False) else "❌"
                
                print(f"{filename:<25} {original:<10} {compressed:<12} {ratio:<8} {verified:<10}")
        
        if successful == len(results) and results:
            print("\n🎉 ALL TESTS PASSED!")
            print("   • Two-stage compression working perfectly")
            print("   • Perfect round-trip reconstruction achieved")  
            print("   • LZSS + Huffman pipeline validated")
        else:
            print(f"\n⚠️  {len(results) - successful} test(s) failed")
    
    else:
        print("No PNG files found for testing.")
    
    print(f"\n🎯 Advanced compression demonstration complete!")


if __name__ == "__main__":
    main() 