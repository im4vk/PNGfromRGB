"""
LZSS (Lempel-Ziv-Storer-Szymanski) Compression Algorithm
=========================================================

This module implements the LZSS lossless data compression algorithm.
LZSS is a variant of LZ77 that uses a sliding window to find repeated
patterns in data and replaces them with references to previous occurrences.

The algorithm maintains:
- A sliding window (lookback buffer) of previously seen data
- A lookahead buffer for finding matches
- A dictionary of recent patterns

Compression output format:
- 1 bit flag: 0 = literal byte, 1 = match reference
- If literal: 8 bits for the byte
- If match: offset (12 bits) + length (4 bits)
"""

import struct
from typing import List, Tuple, Optional


class LZSSCompressor:
    """LZSS Compression implementation."""
    
    def __init__(self, window_size: int = 4096, lookahead_size: int = 15):
        """
        Initialize LZSS compressor.
        
        Args:
            window_size: Size of the sliding window (default 4096)
            lookahead_size: Size of the lookahead buffer (default 15)
        """
        self.window_size = window_size
        self.lookahead_size = lookahead_size
        self.min_match_length = 3  # Minimum length for a match to be worthwhile
    
    def find_longest_match(self, data: bytes, pos: int) -> Tuple[int, int]:
        """
        Find the longest match in the sliding window.
        
        Args:
            data: Input data
            pos: Current position in data
            
        Returns:
            Tuple of (offset, length) of the longest match
        """
        best_offset = 0
        best_length = 0
        
        # Define search window bounds
        start = max(0, pos - self.window_size)
        end = pos
        
        # Maximum length we can match
        max_length = min(self.lookahead_size, len(data) - pos)
        
        # Search for matches in the sliding window
        for i in range(start, end):
            length = 0
            
            # Find how long the match extends
            while (length < max_length and 
                   pos + length < len(data) and
                   data[i + length] == data[pos + length]):
                length += 1
            
            # Update best match if this is longer
            if length >= self.min_match_length and length > best_length:
                best_length = length
                best_offset = pos - i
        
        return best_offset, best_length
    
    def compress(self, data: bytes) -> bytearray:
        """
        Compress data using LZSS algorithm.
        
        Args:
            data: Input data to compress
            
        Returns:
            Compressed data as bytearray
        """
        if not data:
            return bytearray()
        
        compressed = bytearray()
        pos = 0
        
        while pos < len(data):
            # Find longest match in sliding window
            offset, length = self.find_longest_match(data, pos)
            
            if (length >= self.min_match_length and 
                offset > 0 and offset <= 4095 and  # Ensure offset fits in 12 bits
                length <= 18):  # Ensure length fits in 4 bits + 3
                
                # Encode as match: flag(1) + offset(12) + length(4)
                # Use 1 byte for flags (8 matches) + data
                compressed.append(0x01)  # Match flag
                # Encode offset and length in 2 bytes
                # offset: 12 bits, length-3: 4 bits (since min length is 3)
                encoded = (offset << 4) | (length - 3)
                
                # Add bounds checking
                if encoded <= 0xFFFF:  # Ensure it fits in 16 bits
                    compressed.extend(struct.pack('>H', encoded))
                    pos += length
                else:
                    # Fall back to literal if encoding would overflow
                    compressed.append(0x00)  # Literal flag
                    compressed.append(data[pos])
                    pos += 1
            else:
                # Encode as literal
                compressed.append(0x00)  # Literal flag
                compressed.append(data[pos])
                pos += 1
        
        return compressed
    
    def decompress(self, compressed_data: bytearray) -> bytearray:
        """
        Decompress LZSS compressed data.
        
        Args:
            compressed_data: Compressed data to decompress
            
        Returns:
            Decompressed data as bytearray
        """
        if not compressed_data:
            return bytearray()
        
        decompressed = bytearray()
        pos = 0
        
        while pos < len(compressed_data):
            # Read flag
            flag = compressed_data[pos]
            pos += 1
            
            if flag == 0x01:  # Match reference
                if pos + 1 >= len(compressed_data):
                    break
                    
                # Read offset and length
                encoded = struct.unpack('>H', compressed_data[pos:pos+2])[0]
                pos += 2
                
                offset = (encoded >> 4) & 0x0FFF
                length = (encoded & 0x000F) + 3  # Add back the 3 we subtracted
                
                # Copy from sliding window
                start_pos = len(decompressed) - offset
                
                # Handle overlapping copies (common in LZSS)
                for i in range(length):
                    if start_pos + i < len(decompressed):
                        decompressed.append(decompressed[start_pos + i])
                    else:
                        # Should not happen in valid data
                        break
                        
            elif flag == 0x00:  # Literal byte
                if pos >= len(compressed_data):
                    break
                decompressed.append(compressed_data[pos])
                pos += 1
        
        return decompressed


class LZSSAnalyzer:
    """Utility class for analyzing LZSS compression performance."""
    
    @staticmethod
    def calculate_compression_ratio(original: bytes, compressed: bytearray) -> float:
        """Calculate compression ratio."""
        if len(original) == 0:
            return 0.0
        return len(compressed) / len(original)
    
    @staticmethod
    def calculate_space_savings(original: bytes, compressed: bytearray) -> float:
        """Calculate space savings as percentage."""
        if len(original) == 0:
            return 0.0
        return (1 - len(compressed) / len(original)) * 100


def demonstrate_lzss():
    """Demonstrate LZSS compression with various test cases."""
    
    compressor = LZSSCompressor()
    
    test_cases = [
        b"Hello, World! Hello, World! This is a test.",
        b"ABABABABABABABABABAB",
        b"The quick brown fox jumps over the lazy dog. " * 3,
        b"a" * 100,
        b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 2,
        b"This is a test. This is a test. This is a test.",
    ]
    
    print("LZSS Compression Demonstration")
    print("=" * 50)
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Original size: {len(test_data)} bytes")
        print(f"Original data: {test_data[:60]}{'...' if len(test_data) > 60 else ''}")
        
        # Compress
        compressed = compressor.compress(test_data)
        print(f"Compressed size: {len(compressed)} bytes")
        
        # Decompress
        decompressed = compressor.decompress(compressed)
        
        # Verify
        if bytes(decompressed) == test_data:
            print("✅ Compression/Decompression successful!")
        else:
            print("❌ Compression/Decompression failed!")
            print(f"Expected length: {len(test_data)}, Got length: {len(decompressed)}")
            if len(decompressed) > 0:
                print(f"Expected: {test_data[:50]}")
                print(f"Got: {bytes(decompressed)[:50]}")
        
        # Statistics
        ratio = LZSSAnalyzer.calculate_compression_ratio(test_data, compressed)
        savings = LZSSAnalyzer.calculate_space_savings(test_data, compressed)
        
        print(f"Compression ratio: {ratio:.3f}")
        print(f"Space savings: {savings:.1f}%")


def compress_file_example():
    """Example of compressing a text file or string."""
    print("\n" + "=" * 50)
    print("File Compression Example:")
    
    # Create compressor
    lzss = LZSSCompressor()
    
    # Example with repetitive text (simulates file content)
    sample_text = open("test.txt", "rb").read()
    
    print(f"Original text size: {len(sample_text)} bytes")
    print(f"Sample content: {sample_text[:100]}...")
    
    # Compress
    compressed = lzss.compress(sample_text)
    print(f"Compressed size: {len(compressed)} bytes")
    
    # Decompress
    decompressed = lzss.decompress(compressed)
    
    # Verify
    success = bytes(decompressed) == sample_text
    print(f"Compression successful: {'✅' if success else '❌'}")
    
    if success:
        ratio = len(compressed) / len(sample_text)
        savings = (1 - ratio) * 100
        print(f"Compression ratio: {ratio:.3f}")
        print(f"Space savings: {savings:.1f}%")
        
        print(f"\nFirst 100 chars of decompressed:")
        print(bytes(decompressed)[:100])


if __name__ == "__main__":
    # Run the demonstration
    # demonstrate_lzss()
    
    # File compression example
    compress_file_example()
    
    # print("\n" + "=" * 50)
    # print("Quick Test:")
    
    # Quick verification test
    # lzss = LZSSCompressor()
    # test_data = b"banana banana banana"
    
    # compressed = lzss.compress(test_data)
    # decompressed = lzss.decompress(compressed)
    
    # print(f"Test: '{test_data.decode()}'")
    # print(f"Original: {len(test_data)} bytes")
    # print(f"Compressed: {len(compressed)} bytes")
    # print(f"Match: {'✅' if bytes(decompressed) == test_data else '❌'}")
    
    # if bytes(decompressed) == test_data:
    #     ratio = len(compressed) / len(test_data)
    #     print(f"Compression ratio: {ratio:.3f} ({(1-ratio)*100:.1f}% savings)")
