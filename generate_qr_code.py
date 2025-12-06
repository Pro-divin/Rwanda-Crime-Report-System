#!/usr/bin/env python3
"""
QR Code Generator for Rwanda Crime Report System
Generates a QR code that links to https://rcrs.onrender.com/
"""

import qrcode
from pathlib import Path
from datetime import datetime

def generate_qr_code(url, output_path=None, size=30, border=4):
    """
    Generate a QR code for the given URL
    
    Args:
        url: The URL to encode in the QR code
        output_path: Where to save the QR code (PNG file)
        size: Size of each box in pixels (default: 30 - large for easy scanning from distance)
        border: Border size in boxes (default: 4)
    
    Returns:
        Path to the generated QR code file
    """
    if output_path is None:
        # Save in the project root with timestamp
        output_path = Path(__file__).parent / f"qr_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    else:
        output_path = Path(output_path)
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR code
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    
    # Add data and generate
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create image with colors
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image
    img.save(output_path)
    print(f"✅ QR code generated successfully!")
    print(f"📁 Saved to: {output_path}")
    print(f"🔗 URL encoded: {url}")
    
    return output_path

if __name__ == "__main__":
    # Generate QR code for the website
    website_url = "https://rcrs.onrender.com/"
    
    # Standard output name
    qr_file = Path(__file__).parent / "rcrs_qr_code.png"
    
    generate_qr_code(website_url, output_path=qr_file)
    
    print(f"\n📱 Scan this QR code with your phone to access the Rwanda Crime Report System!")
    print(f"🌐 Direct link: {website_url}")
