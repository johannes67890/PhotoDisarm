"""
File utilities for PhotoDisarm

Provides file and image handling utilities.
"""
from datetime import datetime
import os
import shutil
from glob import glob
from pathlib import Path
from typing import List, Generator, Tuple, Optional, Any
from PIL import Image, ExifTags
import tkinter as tk


def center_window(window: tk.Tk, width: int = 500, height: int = 400) -> None:
    """
    Center a tkinter window on the screen
    
    Args:
        window: The tkinter window to center
        width: Desired width of the window
        height: Desired height of the window
    """
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calculate position
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    # Set window size and position
    window.geometry(f"{width}x{height}+{x}+{y}")


def get_images(directory: str, chunk_size: int = 25, 
               valid_exts: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".nef")) -> Generator[List[str], None, None]:
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


def get_images_rec(directory: str, chunk_size: int = 25,
                   valid_exts: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".nef")) -> Generator[List[str], None, None]:
    """
    Get images recursively from a directory in chunks
    
    Args:
        directory: Directory to search
        chunk_size: Number of image paths to yield at once
        valid_exts: Tuple of valid file extensions to include
        
    Returns:
        Generator yielding chunks of image paths
    """
    chunk = []
    
    for ext in valid_exts:
        # Case insensitive search
        pattern = os.path.join(directory, f"**/*{ext}")
        pattern_upper = os.path.join(directory, f"**/*{ext.upper()}")
        
        # First search with lowercase extension
        for path in glob(pattern, recursive=True):
            chunk.append(path)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
                
        # Then with uppercase extension
        for path in glob(pattern_upper, recursive=True):
            chunk.append(path)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
    
    # Yield any remaining images
    if chunk:
        yield chunk


def get_image_metadata_date(image_path: str) -> Optional[str]:
    """
    Get the creation date of an image from its metadata
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Date string if found, None otherwise
    """
    try:
        # For .jpg/.jpeg files, try to get EXIF data
        if image_path.lower().endswith(('.jpg', '.jpeg')):
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    for tag, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag, tag)
                        if tag_name == 'DateTimeOriginal':
                            # Parse date from format like '2021:05:10 15:30:00'
                            dt = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                            return dt.strftime('%Y-%m-%d')
        
        # For NEF files or if EXIF failed, try file creation/modification date
        stat = os.stat(image_path)
        
        # Use the older of creation and modification time
        # (some filesystems don't store creation time accurately)
        try:
            # ctime is creation time on Windows, but not on Unix
            creation_time = datetime.fromtimestamp(stat.st_ctime)
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Use the older date
            date_to_use = min(creation_time, mod_time)
            return date_to_use.strftime('%Y-%m-%d')
        except:
            # If datetime parsing fails
            return None
            
    except Exception as e:
        print(f"Error getting date for {image_path}: {e}")
        return None


def sort_images_by_date(image_paths: List[str]) -> List[str]:
    """
    Sort images by their metadata date
    
    Args:
        image_paths: List of paths to images
        
    Returns:
        Sorted list of image paths
    """
    # Create a list of tuples (path, date) where date might be None
    dated_paths = [(path, get_image_metadata_date(path)) for path in image_paths]
    
    # Sort by date (None dates will be sorted to the end)
    dated_paths.sort(key=lambda x: (x[1] is None, x[1]))
    
    # Return just the sorted paths
    return [path for path, _ in dated_paths]


def move_image_to_dir_with_date(image_path: str, base_output_dir: str) -> str:
    """
    Move an image to a directory structure based on its date
    
    Args:
        image_path: Path to the image file
        base_output_dir: Base directory for output
        
    Returns:
        New path of the moved image
    """
    # Get image date
    image_date = get_image_metadata_date(image_path)
    
    if image_date:
        # Parse date components
        try:
            date_obj = datetime.strptime(image_date, '%Y-%m-%d')
            year = date_obj.strftime('%Y')
            month = date_obj.strftime('%b')  # Month as three letter abbreviation
            
            # Create directory structure: output/YYYY/Mon/
            output_dir = os.path.join(base_output_dir, year, month)
        except:
            # If date parsing fails
            output_dir = os.path.join(base_output_dir, "No Date")
    else:
        # No date found
        output_dir = os.path.join(base_output_dir, "No Date")
    
    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Move the file
    filename = os.path.basename(image_path)
    new_path = os.path.join(output_dir, filename)
    
    # Handle duplicate filenames
    counter = 1
    base_name, ext = os.path.splitext(filename)
    while os.path.exists(new_path):
        new_path = os.path.join(output_dir, f"{base_name}_{counter}{ext}")
        counter += 1
    
    # Move file to the new location
    shutil.move(image_path, new_path)
    
    return new_path
