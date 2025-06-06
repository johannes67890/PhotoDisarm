import os
from PIL import Image, ExifTags
from datetime import datetime
import shutil
from glob import glob
from . import dub as dup
import tkinter as tk
import cv2
from glob import glob
from pathlib import Path


# If you want an even more memory-efficient approach using generators:
def get_images(directory, chunk_size=25, valid_exts=(".jpg", ".jpeg", ".png", ".bmp", ".nef")):
    """
    Get images from a directory in chunks to balance memory usage and processing efficiency.
    
    Args:
        directory: Directory to search
        chunk_size: Number of image paths to yield at once
        valid_exts: Tuple of valid file extensions to include
        
    Returns:
        Generator yielding chunks of image paths
    """
    directory_path = Path(directory)
    chunk = []
    
    for ext in valid_exts:
        for path in directory_path.glob(f"*{ext}"):
            chunk.append(str(path))
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
    
    # Yield any remaining images
    if chunk:
        yield chunk

def get_images_rec(directory, chunk_size=25, valid_exts=(".jpg", ".jpeg", ".png", ".bmp", ".nef")):
    """
    Recursively get all image files from a directory and its subdirectories in chunks.
    
    Args:
        directory: Root directory to search
        chunk_size: Number of image paths to yield at once
        valid_exts: Tuple of valid file extensions to include
        
    Returns:
        Generator yielding chunks of image paths from recursive search
    """
    directory_path = Path(directory)
    chunk = []
    
    for ext in valid_exts:
        for path in directory_path.rglob(f"*{ext}"):
            chunk.append(str(path))
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
    
    # Yield any remaining images
    if chunk:
        yield chunk

def get_image_metadata_date(image_path):
    # Open the image file
    with open(image_path, "rb") as file:
        image = Image.open(file)
        print(image)
        # Get the image's Exif data
        exif_data = image.getexif()
        print(exif_data)
        if exif_data is not None:
            # Get only DateTimeOriginal tag from the Exif data
            for tag_id, value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal" or tag == "DateTime":
                    return value
    return None
                

def printDateOnWindow(image):
    date = get_image_metadata_date(image)
    if date is None:
        return
    (text_width, text_height), baseline = cv2.getTextSize(date, cv2.FONT_ITALIC, 0.8, 2)
    text_x = 10
    text_y = 10
    cv2.rectangle(image, (text_x - 5, text_y - text_height - baseline), (text_x + text_width + 5, text_y + 5), (255, 255, 255), -1)
    cv2.putText(image, f"{date}", (text_x, text_y), cv2.FONT_ITALIC, 0.8, (0, 0, 0), 2)

# Returns a list of image paths sorted by their creation date
def sort_images_by_date(image_paths: list):
    return sorted(image_paths, key=lambda x: os.path.getctime(x))


def move_image_to_dir_with_date(image_path) -> str:
    new_path = None
    if get_image_metadata_date(image_path) is None:
        new_path = os.path.join(os.path.dirname(image_path), "No Date")
    else:
        date = datetime.strptime(get_image_metadata_date(image_path), "%Y:%m:%d %H:%M:%S")
        new_path = os.path.join(os.path.dirname(image_path), date.strftime("%Y"), date.strftime("%b"))

    print(f"Moving image to {os.path.dirname(new_path)}")
    if not os.path.exists(new_path):
        os.makedirs(new_path, exist_ok=True)
    shutil.move(image_path, new_path)
    
    return os.path.join(new_path, os.path.basename(image_path))


def center_window(window: tk.Tk, width=500, height=250):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")