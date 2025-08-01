"""
PNG Data Generator
==================

This module generates PNG image data from scratch, demonstrating the PNG file format
and how compression algorithms like LZSS could be integrated.

PNG file structure:
1. PNG Signature (8 bytes)
2. IHDR chunk (Image Header)
3. IDAT chunk(s) (Image Data - compressed)
4. IEND chunk (End marker)

Each chunk has: Length (4) + Type (4) + Data (variable) + CRC (4)
"""

import struct
import zlib
import math
from typing import List, Tuple, Optional
from main import LZSSCompressor


class PNGGenerator:
    """Generate PNG image data from scratch."""
    
    # PNG signature
    PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
    
    def __init__(self):
        """Initialize PNG generator."""
        self.lzss = LZSSCompressor()
    
    def calculate_crc(self, type_and_data: bytes) -> int:
        """Calculate CRC32 for PNG chunk."""
        return zlib.crc32(type_and_data) & 0xffffffff
    
    def create_chunk(self, chunk_type: bytes, data: bytes) -> bytes:
        """Create a PNG chunk with length, type, data, and CRC."""
        length = struct.pack('>I', len(data))
        type_and_data = chunk_type + data
        crc = struct.pack('>I', self.calculate_crc(type_and_data))
        return length + type_and_data + crc
    
    def create_ihdr_chunk(self, width: int, height: int, bit_depth: int = 8, 
                         color_type: int = 2, compression: int = 0, 
                         filter_method: int = 0, interlace: int = 0) -> bytes:
        """
        Create IHDR (Image Header) chunk.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            bit_depth: Bits per sample (1, 2, 4, 8, 16)
            color_type: 0=grayscale, 2=RGB, 3=palette, 4=grayscale+alpha, 6=RGBA
            compression: Compression method (0 = deflate)
            filter_method: Filter method (0 = adaptive filtering)
            interlace: Interlace method (0 = no interlace, 1 = Adam7)
        """
        ihdr_data = struct.pack('>IIBBBBB', width, height, bit_depth, 
                               color_type, compression, filter_method, interlace)
        return self.create_chunk(b'IHDR', ihdr_data)
    
    def apply_filter(self, scanline: bytes, filter_type: int = 0) -> bytes:
        """Apply PNG filter to a scanline."""
        # Filter type 0 = None (no filtering)
        return bytes([filter_type]) + scanline
    
    def create_rgb_image_data(self, width: int, height: int, 
                             rgb_func=None) -> bytes:
        """
        Create RGB image data.
        
        Args:
            width: Image width
            height: Image height  
            rgb_func: Function that takes (x, y) and returns (r, g, b) tuple
        """
        if rgb_func is None:
            # Default: create a gradient pattern
            rgb_func = lambda x, y: (
                int(255 * x / width),           # Red gradient
                int(255 * y / height),          # Green gradient
                int(255 * ((x + y) % 256) / 255)  # Blue pattern
            )
        
        image_data = bytearray()
        
        for y in range(height):
            scanline = bytearray()
            for x in range(width):
                r, g, b = rgb_func(x, y)
                scanline.extend([r & 0xFF, g & 0xFF, b & 0xFF])
            
            # Apply filter (filter type 0 = no filter)
            filtered_scanline = self.apply_filter(bytes(scanline), 0)
            image_data.extend(filtered_scanline)
        
        return bytes(image_data)
    
    def compress_image_data(self, image_data: bytes, method: str = 'zlib') -> bytes:
        """
        Compress image data using specified method.
        
        Args:
            image_data: Raw image data
            method: 'zlib' (standard) or 'lzss' (our implementation)
        """
        if method == 'zlib':
            # Standard PNG compression (DEFLATE)
            return zlib.compress(image_data, level=6)
        elif method == 'lzss':
            # Our LZSS implementation (for demonstration)
            compressed = self.lzss.compress(image_data)
            return bytes(compressed)
        else:
            raise ValueError(f"Unknown compression method: {method}")
    
    def create_idat_chunk(self, compressed_data: bytes) -> bytes:
        """Create IDAT (Image Data) chunk."""
        return self.create_chunk(b'IDAT', compressed_data)
    
    def create_iend_chunk(self) -> bytes:
        """Create IEND (End) chunk."""
        return self.create_chunk(b'IEND', b'')
    
    def generate_png(self, width: int, height: int, rgb_func=None, 
                    compression_method: str = 'zlib') -> bytes:
        """
        Generate a complete PNG image.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            rgb_func: Function to generate RGB values at each pixel
            compression_method: 'zlib' or 'lzss'
        
        Returns:
            Complete PNG file data as bytes
        """
        png_data = bytearray()
        
        # 1. PNG Signature
        png_data.extend(self.PNG_SIGNATURE)
        
        # 2. IHDR Chunk
        ihdr_chunk = self.create_ihdr_chunk(width, height, bit_depth=8, color_type=2)
        png_data.extend(ihdr_chunk)
        
        # 3. Create and compress image data
        image_data = self.create_rgb_image_data(width, height, rgb_func)
        compressed_data = self.compress_image_data(image_data, compression_method)
        
        # 4. IDAT Chunk
        idat_chunk = self.create_idat_chunk(compressed_data)
        png_data.extend(idat_chunk)
        
        # 5. IEND Chunk
        iend_chunk = self.create_iend_chunk()
        png_data.extend(iend_chunk)
        
        return bytes(png_data)


def create_gradient_image() -> bytes:
    """Create a gradient PNG image."""
    generator = PNGGenerator()
    
    def gradient_rgb(x: int, y: int) -> Tuple[int, int, int]:
        """Create a colorful gradient pattern."""
        r = int(255 * (x / 100))
        g = int(255 * (y / 100))
        b = int(255 * ((x + y) / 200))
        return (r, g, b)
    
    return generator.generate_png(100, 100, gradient_rgb)


def create_pattern_image() -> bytes:
    """Create a geometric pattern PNG image.""" 
    generator = PNGGenerator()
    
    def pattern_rgb(x: int, y: int) -> Tuple[int, int, int]:
        """Create a checkerboard-like pattern."""
        # Checkerboard pattern
        check_size = 10
        is_black = ((x // check_size) + (y // check_size)) % 2 == 0
        
        if is_black:
            return (0, 0, 0)  # Black
        else:
            # Colorful squares
            r = (x * 7) % 256
            g = (y * 11) % 256  
            b = ((x + y) * 13) % 256
            return (r, g, b)
    
    return generator.generate_png(80, 80, pattern_rgb)


def create_circle_image() -> bytes:
    """Create a PNG with a circle pattern."""
    generator = PNGGenerator()
    
    def circle_rgb(x: int, y: int) -> Tuple[int, int, int]:
        """Create concentric circles."""
        center_x, center_y = 64, 64
        distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        # Create concentric circles
        circle_intensity = int((math.sin(distance / 8) + 1) * 127.5)
        
        # Color based on angle
        angle = math.atan2(y - center_y, x - center_x)
        r = int((math.sin(angle) + 1) * 127.5)
        g = int((math.cos(angle) + 1) * 127.5) 
        b = circle_intensity
        
        return (r, g, b)
    
    return generator.generate_png(128, 128, circle_rgb)


def demonstrate_png_generation():
    """Demonstrate PNG generation with different patterns."""
    generator = PNGGenerator()
    
    print("PNG Data Generation Demonstration")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        ("Gradient", create_gradient_image),
        ("Pattern", create_pattern_image), 
        ("Circles", create_circle_image),
    ]
    
    for name, create_func in test_cases:
        print(f"\n{name} Image:")
        
        # Generate PNG
        png_data = create_func()
        print(f"PNG file size: {len(png_data)} bytes")
        
        # Save to file
        filename = f"{name.lower()}_image.png"
        with open(filename, 'wb') as f:
            f.write(png_data)
        print(f"Saved as: {filename}")
        
        # Analyze PNG structure
        print(f"PNG signature: {png_data[:8].hex()}")
        print(f"First chunk type: {png_data[12:16]}")
        
        # Test with different compression
        print("\nCompression comparison:")
        
        # Standard PNG (zlib)
        standard_png = generator.generate_png(50, 50, compression_method='zlib')
        print(f"  Standard (zlib): {len(standard_png)} bytes")
        
        # LZSS compression  
        lzss_png = generator.generate_png(50, 50, compression_method='lzss')
        print(f"  LZSS: {len(lzss_png)} bytes")
        
        ratio = len(lzss_png) / len(standard_png)
        print(f"  LZSS vs Standard ratio: {ratio:.3f}")


def analyze_png_structure(png_data: bytes):
    """Analyze and display PNG file structure."""
    print("\nPNG Structure Analysis:")
    print("-" * 30)
    
    pos = 0
    
    # Check signature
    signature = png_data[pos:pos+8]
    print(f"Signature: {signature.hex()} {'✅' if signature == PNGGenerator.PNG_SIGNATURE else '❌'}")
    pos += 8
    
    # Parse chunks
    chunk_num = 1
    while pos < len(png_data):
        if pos + 8 > len(png_data):
            break
            
        # Read chunk header
        length = struct.unpack('>I', png_data[pos:pos+4])[0]
        chunk_type = png_data[pos+4:pos+8]
        
        print(f"Chunk {chunk_num}: {chunk_type.decode('ascii', errors='ignore')} ({length} bytes)")
        
        pos += 8 + length + 4  # Skip header + data + CRC
        chunk_num += 1
        
        if chunk_type == b'IEND':
            break


if __name__ == "__main__":
    # Run demonstrations
    demonstrate_png_generation()
    
    print("\n" + "=" * 50)
    print("Custom PNG Example:")
    
    # Create a custom image
    generator = PNGGenerator()
    
    def custom_pattern(x: int, y: int) -> Tuple[int, int, int]:
        """Custom RGB pattern."""
        return (
            (x * 3) % 256,      # Red channel
            (y * 5) % 256,      # Green channel  
            ((x ^ y) * 2) % 256 # Blue channel (XOR pattern)
        )
    
    custom_png = generator.generate_png(60, 60, custom_pattern)
    
    # Save and analyze
    with open('custom_pattern.png', 'wb') as f:
        f.write(custom_png)
    
    print(f"Custom PNG created: {len(custom_png)} bytes")
    print("Saved as: custom_pattern.png")
    
    # Analyze structure
    analyze_png_structure(custom_png) 