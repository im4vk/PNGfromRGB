#!/usr/bin/env python3
"""
PNG Data Generation Demo
========================

Simple demonstration of generating PNG images with different patterns.
"""

from png_generator import PNGGenerator
import math


def main():
    """Generate various PNG images."""
    print("🎨 PNG Data Generation Demo")
    print("=" * 40)
    
    generator = PNGGenerator()
    
    # Demo 1: Simple gradient
    print("\n1. Creating gradient image...")
    def gradient(x, y):
        return (x * 255 // 50, y * 255 // 50, 128)
    
    png_data = generator.generate_png(50, 50, gradient)
    with open('demo_gradient.png', 'wb') as f:
        f.write(png_data)
    print(f"   ✅ Created demo_gradient.png ({len(png_data)} bytes)")
    
    # Demo 2: Checkerboard
    print("\n2. Creating checkerboard...")
    def checkerboard(x, y):
        if (x // 8 + y // 8) % 2:
            return (255, 255, 255)  # White
        else:
            return (0, 0, 0)        # Black
    
    png_data = generator.generate_png(64, 64, checkerboard)
    with open('demo_checkerboard.png', 'wb') as f:
        f.write(png_data)
    print(f"   ✅ Created demo_checkerboard.png ({len(png_data)} bytes)")
    
    # Demo 3: Mandelbrot-like pattern
    print("\n3. Creating mathematical pattern...")
    def mandelbrot_pattern(x, y):
        # Simple mathematical visualization
        cx, cy = (x - 32) / 16, (y - 32) / 16
        z = complex(0, 0)
        c = complex(cx, cy)
        
        for i in range(20):
            if abs(z) > 2:
                break
            z = z*z + c
        
        intensity = i * 12 % 256
        return (intensity, intensity // 2, 255 - intensity)
    
    png_data = generator.generate_png(64, 64, mandelbrot_pattern)
    with open('demo_mandelbrot.png', 'wb') as f:
        f.write(png_data)
    print(f"   ✅ Created demo_mandelbrot.png ({len(png_data)} bytes)")
    
    # Demo 4: Rainbow spiral
    print("\n4. Creating rainbow spiral...")
    def rainbow_spiral(x, y):
        center_x, center_y = 50, 50
        dx, dy = x - center_x, y - center_y
        
        # Calculate angle and distance
        angle = math.atan2(dy, dx)
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Create spiral effect
        spiral = angle + distance * 0.1
        
        r = int((math.sin(spiral) + 1) * 127.5)
        g = int((math.sin(spiral + 2.1) + 1) * 127.5)
        b = int((math.sin(spiral + 4.2) + 1) * 127.5)
        
        return (r, g, b)
    
    png_data = generator.generate_png(100, 100, rainbow_spiral)
    with open('demo_rainbow_spiral.png', 'wb') as f:
        f.write(png_data)
    print(f"   ✅ Created demo_rainbow_spiral.png ({len(png_data)} bytes)")
    
    # Demo 5: Compare compression methods
    print("\n5. Comparing compression methods...")
    
    # Create test pattern with repetition (good for compression)
    def repeating_pattern(x, y):
        pattern_x = x % 16
        pattern_y = y % 16
        if pattern_x < 8 and pattern_y < 8:
            return (255, 0, 0)      # Red
        elif pattern_x >= 8 and pattern_y < 8:
            return (0, 255, 0)      # Green  
        elif pattern_x < 8 and pattern_y >= 8:
            return (0, 0, 255)      # Blue
        else:
            return (255, 255, 0)    # Yellow
    
    # Standard compression
    png_standard = generator.generate_png(80, 80, repeating_pattern, 'zlib')
    with open('demo_standard_compression.png', 'wb') as f:
        f.write(png_standard)
    
    # LZSS compression  
    png_lzss = generator.generate_png(80, 80, repeating_pattern, 'lzss')
    with open('demo_lzss_compression.png', 'wb') as f:
        f.write(png_lzss)
    
    print(f"   📊 Standard (zlib): {len(png_standard)} bytes")
    print(f"   📊 LZSS: {len(png_lzss)} bytes")
    print(f"   📊 LZSS vs Standard: {len(png_lzss)/len(png_standard):.2f}x")
    
    print("\n🎉 All PNG images generated successfully!")
    print("\nGenerated files:")
    print("  - demo_gradient.png")
    print("  - demo_checkerboard.png") 
    print("  - demo_mandelbrot.png")
    print("  - demo_rainbow_spiral.png")
    print("  - demo_standard_compression.png")
    print("  - demo_lzss_compression.png")


if __name__ == "__main__":
    main() 