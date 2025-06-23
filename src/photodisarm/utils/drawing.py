"""
Image drawing utilities for PhotoDisarm

Provides text rendering on images with UTF-8 support.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from typing import Tuple, List, Optional


def put_text_utf8(img: np.ndarray, text: str, position: Tuple[int, int], 
                 font_size: int = 30, color: Tuple[int, int, int] = (255, 255, 255), 
                 thickness: int = 2, with_background: bool = True) -> np.ndarray:
    """
    Draw text with UTF-8 support (for characters like æ, ø, å) and improved visibility
    with sharp text rendering, adaptive thickness, and a subtle shadow.
    
    Args:
        img: OpenCV image (numpy array)
        text: UTF-8 text to display
        position: (x, y) position for the text
        font_size: Size of the font
        color: (B, G, R) color tuple
        thickness: Text thickness
        with_background: Whether to add a semi-transparent background behind text
        
    Returns:
        Modified image with text
    """
    # Create a PIL Image from the OpenCV image (converting BGR to RGB)
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    
    # Try to use a font that supports Danish characters
    try:
        # Try to find a system font that supports Danish characters
        font_path = None
        potential_fonts = [
            # Windows fonts - prioritize ClearType-optimized fonts
            "C:/Windows/Fonts/segoeui.ttf",  # Segoe UI (clearer on screens)
            "C:/Windows/Fonts/calibri.ttf",  # Calibri
            "C:/Windows/Fonts/arial.ttf",    # Arial
            # Mac fonts
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/SFCompact.ttf",
            # Linux fonts
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]
        
        for path in potential_fonts:
            if os.path.exists(path):
                font_path = path
                break
        
        # Use the found font or fall back to default
        if font_path:
            # Create a slightly larger font for better rendering quality when scaled
            render_size = int(font_size * 1.2)
            font = ImageFont.truetype(font_path, render_size)
        else:
            # Fall back to default font
            font = ImageFont.load_default()
            
    except Exception as e:
        print(f"Error loading font: {e}")
        font = ImageFont.load_default()
    
    # Get text size for background
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Determine adaptive thickness based on font size
    adaptive_thickness = max(1, thickness)
    if font_size > 24:
        adaptive_thickness = max(2, thickness)
    
    # Calculate shadow offset (subtle shadow for improved readability)
    shadow_offset = max(1, int(font_size / 15))
    
    # Draw semi-transparent background if requested
    if with_background:
        # Create a semitransparent black background rectangle with rounded corners
        overlay = pil_img.copy()
        draw = ImageDraw.Draw(overlay)
        bg_padding = 8  # Slightly larger padding
        bg_coords = [
            position[0] - bg_padding,  # x1
            position[1] - bg_padding,  # y1
            position[0] + text_width + bg_padding,  # x2
            position[1] + text_height + bg_padding   # y2
        ]
        
        # Create a semi-transparent black background
        draw.rectangle(bg_coords, fill=(0, 0, 0, 180))  # Slightly more opaque
        
        # Combine the original image with the overlay
        pil_img = Image.alpha_composite(pil_img.convert('RGBA'), overlay.convert('RGBA')).convert('RGB')
        draw = ImageDraw.Draw(pil_img)
    
    # Draw a subtle shadow for improved readability against any background
    draw.text((position[0] + shadow_offset, position[1] + shadow_offset), 
              text, font=font, fill=(0, 0, 0), stroke_width=0)
    
    # Draw the main text on the PIL image with the adaptive stroke thickness
    draw.text(position, text, font=font, fill=color[::-1], stroke_width=adaptive_thickness)
    
    # Convert back to OpenCV format (RGB to BGR)
    result_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return result_img
