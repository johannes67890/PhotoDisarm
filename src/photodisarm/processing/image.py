import cv2
import rawpy
import numpy as np
import os
from PIL import Image
from glob import glob
from multiprocessing import Pool, cpu_count
import hashlib
import pickle
import time
from photodisarm.ui.canvas import display_message, put_text_utf8, resize_image

class Image_processing:
    def __init__(self):
        # Cache directory for processed NEF files
        self.CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    @staticmethod
    def variance_of_laplacian(image):
        return cv2.Laplacian(image, cv2.CV_64F).var()

    @staticmethod
    def get_cache_path(file_path):
        """Generate a unique cache path based on file path and modification time"""
        # Define cache directory as a static path
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        file_stat = os.stat(file_path)
        hash_input = f"{file_path}_{file_stat.st_mtime}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()
        return os.path.join(cache_dir, f"{file_hash}.pkl")


    @staticmethod
    def process_image(path:str, max_width, max_height, use_cache=True, quality='normal'):
        """
        Process an image file with optimizations for NEF files.
        
        Args:
            path: Path to the image file
            max_width: Maximum width for display
            max_height: Maximum height for display
            use_cache: Whether to use cached versions of processed NEF files
            quality: Image quality - 'low', 'normal', or 'high'
        """
        try:
            # For NEF files, check cache first if enabled
            if path.lower().endswith('.nef'):
                if use_cache:
                    cache_path = Image_processing.get_cache_path(path)
                    if os.path.exists(cache_path):
                        try:
                            with open(cache_path, 'rb') as f:
                                cached_data = pickle.load(f)
                                return path, cached_data
                        except Exception as e:
                            print(f"Cache error for {path}: {e}")
                            # Continue to process if cache fails
                
                # Process the NEF file
                start_time = time.time()
                print(f"Processing NEF file: {os.path.basename(path)}")
                
                with rawpy.imread(path) as raw:
                    # Use different processing options based on quality setting
                    if quality == 'low':
                        # Faster processing with lower quality
                        rgb_image = raw.postprocess(use_camera_wb=True, half_size=True, 
                                                demosaic_algorithm=rawpy.DemosaicAlgorithm.LINEAR)
                    elif quality == 'high':
                        # Higher quality but slower
                        rgb_image = raw.postprocess(use_camera_wb=True, no_auto_bright=False,
                                                demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD)
                    else:  # normal
                        # Balanced approach
                        rgb_image = raw.postprocess(use_camera_wb=True)
                
                # Convert to BGR (OpenCV format)
                image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
                
                # Save to cache if enabled
                if use_cache:
                    # Resize immediately to reduce cache size
                    resized_image = resize_image(image, max_width, max_height)
                    try:
                        with open(cache_path, 'wb') as f:
                            pickle.dump(resized_image, f)
                        print(f"Cached NEF processing result: {time.time() - start_time:.2f} seconds")
                        return path, resized_image
                    except Exception as e:
                        print(f"Failed to cache result for {path}: {e}")
            else:
                # For non-NEF files, use standard OpenCV
                image = cv2.imread(path)
            
            # Resize for display
            resized_image = resize_image(image, max_width, max_height)
            return path, resized_image
        except Exception as e:
            print(f"Error processing {path}: {e}")
            return None, None

    @staticmethod
    def process_images_parallel(image_paths, max_width, max_height, use_cache=True, quality='normal', max_workers=None):
        """
        Process multiple images in parallel using a process pool.
        
        Args:
            image_paths: List of image paths to process
            max_width: Maximum width for display
            max_height: Maximum height for display
            use_cache: Whether to use cached versions of processed NEF files
            quality: Image quality - 'low', 'normal', or 'high'
            max_workers: Maximum number of worker processes (default: CPU count)
        
        Returns:
            List of (path, image) tuples for successfully processed images
        """
        if max_workers is None:
            max_workers = max(1, cpu_count() - 1)  # Leave one CPU free
        
        with Pool(processes=max_workers) as pool:
            # Create a list of argument tuples for each image
            args = [(path, max_width, max_height, use_cache, quality) for path in image_paths]
            # Process images in parallel
            results = pool.starmap(Image_processing.process_image_wrapper, args)
        
        # Filter out failed results
        return [result for result in results if result[1] is not None]

    @staticmethod
    def process_image_wrapper(path, max_width, max_height, use_cache=True, quality='normal'):
        """Wrapper function for process_image to use with multiprocessing"""
        return Image_processing.process_image(path, max_width, max_height, use_cache, quality)


    @staticmethod
    def detect_blurry_images(image_paths, threshold=100, max_workers=None):
        """
        Detect blurry images from a list of image paths.
        
        Args:
            image_paths: List of image paths to check
            threshold: Laplacian variance threshold below which an image is considered blurry
            max_workers: Maximum number of worker processes
        
        Returns:
            List of paths to images detected as blurry
        """
        if max_workers is None:
            max_workers = max(1, cpu_count() - 1)  # Leave one CPU free
        
        # Process images at lower quality for blur detection
        processed_images = Image_processing.process_images_parallel(
            image_paths, 1024, 1024, use_cache=True, quality='low', max_workers=max_workers
        )
        
        blurry_images = []
        for path, image in processed_images:
            # Convert to grayscale for Laplacian calculation
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Calculate variance of Laplacian
            variance = Image_processing.variance_of_laplacian(gray)
            # If variance is below threshold, image is considered blurry
            if variance < threshold:
                blurry_images.append(path)
        
        return blurry_images




