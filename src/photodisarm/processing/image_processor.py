"""
Image processing module for PhotoDisarm

Provides functions for loading, processing, and analyzing images.
"""
import cv2
import rawpy
import numpy as np
import os
from PIL import Image
import hashlib
import pickle
import time
from typing import Tuple, List, Dict, Optional, Any

# Cache directory for processed NEF files
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)


def variance_of_laplacian(image: np.ndarray) -> float:
    """
    Calculate the variance of Laplacian for an image
    
    Args:
        image: The input image
        
    Returns:
        Variance of Laplacian value (higher = more in focus)
    """
    return cv2.Laplacian(image, cv2.CV_64F).var()


def get_cache_path(file_path: str) -> str:
    """
    Generate a unique cache path based on file path and modification time
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Path to the cache file
    """
    file_stat = os.stat(file_path)
    hash_input = f"{file_path}_{file_stat.st_mtime}"
    file_hash = hashlib.md5(hash_input.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{file_hash}.pkl")


def process_image(path: str, max_width: int, max_height: int, 
                 use_cache: bool = True, quality: str = 'normal') -> Tuple[str, Optional[np.ndarray]]:
    """
    Process an image file, handling various formats and optimizing for performance
    
    Args:
        path: Path to the image file
        max_width: Maximum display width
        max_height: Maximum display height
        use_cache: Whether to use the cache for NEF files
        quality: Processing quality ('low', 'normal', or 'high')
        
    Returns:
        Tuple of (path, image_data)
    """
    try:
        start_time = time.time()
        cache_path = None
        
        # Check if this is a NEF file
        if path.lower().endswith('.nef'):
            if use_cache:
                # Check if we have a cached version
                cache_path = get_cache_path(path)
                if os.path.exists(cache_path):
                    try:
                        with open(cache_path, 'rb') as f:
                            image_data = pickle.load(f)
                            # Ensure the cached image is the right size
                            h, w = image_data.shape[:2]
                            if h > max_height or w > max_width:
                                # Resize if needed
                                image_data = resize_image_to_fit(image_data, max_width, max_height)
                            return path, image_data
                    except Exception as e:
                        print(f"Cache loading error for {path}: {e}")
            
            # Process NEF file with different quality settings
            if quality == 'low':
                # Low quality - faster but lower quality
                with rawpy.imread(path) as raw:
                    # Use fast, low quality processing
                    img = raw.postprocess(
                        use_camera_wb=True,
                        half_size=True,
                        no_auto_bright=True,
                        output_bps=8
                    )
            elif quality == 'high':
                # High quality - slower but better results
                with rawpy.imread(path) as raw:
                    # Use high quality processing
                    img = raw.postprocess(
                        use_camera_wb=True,
                        demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
                        fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Full,
                        output_bps=16
                    )
            else:
                # Normal quality (default) - balanced
                with rawpy.imread(path) as raw:
                    # Use standard processing
                    img = raw.postprocess(use_camera_wb=True)
            
            # Convert from RGB to BGR for OpenCV compatibility
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
        else:
            # Regular image file (JPEG, PNG, etc.)
            img = cv2.imread(path)
            if img is None:
                print(f"Failed to load image: {path}")
                return path, None
        
        # Resize the image to fit within max dimensions
        image_data = resize_image_to_fit(img, max_width, max_height)
        
        # Cache the processed NEF file if enabled
        if path.lower().endswith('.nef') and use_cache and cache_path:
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(image_data, f)
            except Exception as e:
                print(f"Error saving to cache: {e}")
        
        # Log processing time for monitoring
        elapsed = time.time() - start_time
        if elapsed > 0.5:  # Only log slow operations
            print(f"Processed {path} in {elapsed:.2f}s (quality={quality}, cached={False})")
            
        return path, image_data
        
    except Exception as e:
        print(f"Error processing image {path}: {e}")
        return path, None


def resize_image_to_fit(image: np.ndarray, max_width: int, max_height: int) -> np.ndarray:
    """
    Resize an image to fit within specified dimensions while preserving aspect ratio
    
    Args:
        image: The input image
        max_width: Maximum allowed width
        max_height: Maximum allowed height
        
    Returns:
        Resized image
    """
    height, width = image.shape[:2]
    
    # Calculate aspect ratios
    aspect = width / height
    target_aspect = max_width / max_height
    
    if aspect > target_aspect:
        # Image is wider than target, scale by width
        new_width = max_width
        new_height = int(new_width / aspect)
    else:
        # Image is taller than target, scale by height
        new_height = max_height
        new_width = int(new_height * aspect)
    
    # Resize the image
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)


def analyze_image_blur(image: np.ndarray) -> float:
    """
    Analyze how blurry an image is
    
    Args:
        image: The input image
        
    Returns:
        Blur score (higher = less blurry)
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
        
    return variance_of_laplacian(gray)
