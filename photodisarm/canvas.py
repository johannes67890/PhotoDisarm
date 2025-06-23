import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def put_text_utf8(img, text, position, font_size=30, color=(255, 255, 255), thickness=2, with_background=True):
    """
    Draw text with UTF-8 support (for characters like æ, ø, å) and improved visibility
    
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
            "arial.ttf",      # Windows
            "Arial.ttf",      # Mac
            "DejaVuSans.ttf", # Linux
            "NotoSans-Regular.ttf",  # Common on many systems
        ]
        
        for font_name in potential_fonts:
            # Check common font locations
            common_paths = [
                os.path.join(os.environ.get('WINDIR', ''), 'Fonts'),  # Windows
                '/usr/share/fonts/truetype',  # Linux
                '/System/Library/Fonts',  # macOS
                '.'  # Current directory
            ]
            
            for path in common_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    possible_path = os.path.join(path, font_name)
                    if os.path.exists(possible_path):
                        font_path = possible_path
                        break
            
            if font_path:
                break
        
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            # Fallback to default font
            font = ImageFont.load_default()
            font_size = 15  # Default font is smaller
    
    except Exception as e:
        print(f"Error loading font: {e}")
        font = ImageFont.load_default()
        font_size = 15  # Default font is smaller
    
    # Get text dimensions to create background
    text_bbox = draw.textbbox(position, text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Add semi-transparent background for better readability
    if with_background:
        # Create a new transparent image for the background
        overlay = Image.new('RGBA', pil_img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Draw a semi-transparent black rectangle behind the text
        padding = 5  # Padding around text
        overlay_draw.rectangle(
            [
                position[0] - padding,
                position[1] - padding,
                position[0] + text_width + padding,
                position[1] + text_height + padding
            ],
            fill=(0, 0, 0, 128)  # Black with 50% opacity
        )
        
        # Composite the overlay with the original image
        pil_img = Image.alpha_composite(pil_img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(pil_img)
    
    # Draw text with the selected font
    draw.text(position, text, font=font, fill=(color[2], color[1], color[0]))
    
    # Convert back to OpenCV format (RGB to BGR)
    result_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    # Alternative option: Draw text with stroke (border) for better visibility
    if not with_background:
        # Drawing with border requires a different approach
        # First draw text with black outline
        for offset_x, offset_y in [(1,1), (-1,-1), (1,-1), (-1,1), (2,0), (-2,0), (0,2), (0,-2)]:
            temp_img = pil_img.copy()
            temp_draw = ImageDraw.Draw(temp_img)
            temp_draw.text(
                (position[0] + offset_x, position[1] + offset_y),
                text,
                font=font,
                fill=(0, 0, 0)  # Black outline
            )
            result_img = cv2.cvtColor(np.array(temp_img), cv2.COLOR_RGB2BGR)
        
        # Then draw main text in original color
        final_img = Image.fromarray(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
        final_draw = ImageDraw.Draw(final_img)
        final_draw.text(position, text, font=font, fill=(color[2], color[1], color[0]))
        result_img = cv2.cvtColor(np.array(final_img), cv2.COLOR_RGB2BGR)
    
    return result_img


def display_message(message, width, height):
    # Create a blank image
    blank_image = np.zeros((height, width, 3), dtype=np.uint8)
    # Set text parameters
    cv2.putText(blank_image, message, (50, height // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    return blank_image


def resize_image(image, max_width, max_height):
    (h, w) = image.shape[:2]
    aspect_ratio = w / h

    # Calculate new dimensions while maintaining aspect ratio
    if w > h:
        new_width = min(w, max_width)
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = min(h, max_height)
        new_width = int(new_height * aspect_ratio)

    # Ensure new dimensions don't exceed the maximum allowed dimensions
    if new_width > max_width or new_height > max_height:
        # Scale down to fit within max dimensions
        scale_factor = min(max_width / w, max_height / h)
        new_width = int(w * scale_factor)
        new_height = int(h * scale_factor)

    # Resize the image to the new dimensions
    resized_image = cv2.resize(image, (new_width, new_height))

    # Create a blank canvas with max dimensions
    canvas = np.zeros((max_height, max_width, 3), dtype=np.uint8)

    # Calculate center position
    y_offset = (max_height - new_height) // 2
    x_offset = (max_width - new_width) // 2

    # Place the resized image on the canvas, if it fits
    canvas[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_image

    return canvas