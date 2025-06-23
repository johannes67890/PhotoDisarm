"""
Background processing module for PhotoDisarm

Provides asynchronous image loading and processing.
"""
import threading
import queue
import time
import os
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

from photodisarm.processing.image_processor import process_image


class BackgroundProcessor:
    """
    Background processor for asynchronous image loading and processing
    
    This class handles preloading and processing images in the background
    to improve application responsiveness, especially for large RAW files.
    """
    
    def __init__(self, max_queue_size: int = 50):
        """
        Initialize the background processor
        
        Args:
            max_queue_size: Maximum size for the processing queue
        """
        self.image_queue = queue.Queue(maxsize=max_queue_size)
        self.processing_thread = None
        self.running = False
        self.current_chunk: List[str] = []
        self.next_chunk: List[str] = []
        self.current_index = 0
        self.chunk_size = 25  # Default chunk size
        self.max_width = 1000
        self.max_height = 800
        self.use_cache = True
        self.quality = 'normal'
        self.processed_images: Dict[str, np.ndarray] = {}  # In-memory cache
    
    def start(self, image_paths: List[str], current_index: int, 
              max_width: int, max_height: int, use_cache: bool = True, 
              quality: str = 'normal', chunk_size: int = 25,
              all_paths: Optional[List[str]] = None, 
              current_chunk_idx: int = 0) -> None:
        """
        Start background processing thread with the given parameters
        
        Args:
            image_paths: List of image paths in current chunk
            current_index: Current image index within chunk
            max_width: Maximum image width
            max_height: Maximum image height
            use_cache: Whether to use caching
            quality: Image quality setting ('low', 'normal', 'high')
            chunk_size: Size of each processing chunk
            all_paths: List of all image paths (for next chunk calculation)
            current_chunk_idx: Index of the current chunk
        """
        self.stop()  # Ensure any previous thread is stopped
        
        self.current_chunk = image_paths
        self.current_index = current_index
        self.max_width = max_width
        self.max_height = max_height
        self.use_cache = use_cache
        self.quality = quality
        self.chunk_size = chunk_size
        self.running = True
        
        # Prepare next chunk if all_paths is provided
        if all_paths is not None and len(all_paths) > (current_chunk_idx + 1) * chunk_size:
            next_start = (current_chunk_idx + 1) * chunk_size
            next_end = min(next_start + chunk_size, len(all_paths))
            self.next_chunk = all_paths[next_start:next_end]
            print(f"Preparing to preload next chunk ({len(self.next_chunk)} images)")
        else:
            self.next_chunk = []
        
        # Clear the queue and in-memory cache (keep only what's still needed)
        self.processed_images = {
            path: img for path, img in self.processed_images.items() 
            if path in self.current_chunk or path in self.next_chunk
        }
        
        while not self.image_queue.empty():
            try:
                self.image_queue.get_nowait()
            except queue.Empty:
                break
                
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_images, daemon=True)
        self.processing_thread.start()
        
        # Print status
        print(f"Background processor started - caching {len(self.current_chunk)} images in current chunk " + 
             f"and {len(self.next_chunk)} images in next chunk")
    
    def stop(self) -> None:
        """Stop the background processing"""
        self.running = False
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=0.5)  # Wait briefly for thread to finish
        
        # Clear the queue
        while not self.image_queue.empty():
            try:
                self.image_queue.get_nowait()
            except queue.Empty:
                break
    
    def get_image(self, image_path: str) -> Tuple[str, Optional[np.ndarray]]:
        """
        Get a processed image either from the cache, queue or by processing it now
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (path, image_data)
        """
        # First check our in-memory cache
        if image_path in self.processed_images:
            return image_path, self.processed_images[image_path]
        
        # Then check if this image is already in the queue
        temp_queue = []
        found = False
        found_data = None
        
        # Search through the queue
        while not self.image_queue.empty() and not found:
            try:
                path, img = self.image_queue.get_nowait()
                if path == image_path:
                    # Found it!
                    found = True
                    found_data = img
                    # Save to in-memory cache for future
                    self.processed_images[path] = img
                else:
                    # Store temporarily
                    temp_queue.append((path, img))
            except queue.Empty:
                break
        
        # Put everything back in the queue
        for item in temp_queue:
            try:
                self.image_queue.put(item)
            except queue.Full:
                # Queue is full, save to in-memory cache at least
                self.processed_images[item[0]] = item[1]
        
        # If we found it, return it
        if found:
            return image_path, found_data
        
        # If we didn't find it, process it now (blocking)
        print(f"Processing image now (not preloaded): {image_path}")
        path, img_data = process_image(
            image_path,
            self.max_width,
            self.max_height,
            use_cache=self.use_cache,
            quality=self.quality
        )
        
        # Add to in-memory cache
        if img_data is not None:
            self.processed_images[path] = img_data
            
        return path, img_data
    
    def _process_images(self) -> None:
        """Background thread that processes upcoming images in both current and next chunk"""
        try:
            # First, cache all images in the current chunk
            current_chunk_processed = 0
            next_chunk_processed = 0
            
            while self.running:
                # Process strategy:
                # 1. Process all remaining images in current chunk
                # 2. Process all images in next chunk
                # 3. If both are done, sleep briefly
                
                # First priority: process remaining images in current chunk
                unprocessed_current = [p for p in self.current_chunk if p not in self.processed_images]
                
                if unprocessed_current:
                    img_path = unprocessed_current[0]
                    # Prioritize NEF files
                    if img_path.lower().endswith('.nef') or len([p for p in unprocessed_current if p.lower().endswith('.nef')]) == 0:
                        try:
                            # Process the image if not in memory cache already
                            if img_path not in self.processed_images:
                                print(f"Preloading current chunk image: {os.path.basename(img_path)}")
                                path, img_data = process_image(
                                    img_path,
                                    self.max_width,
                                    self.max_height,
                                    use_cache=self.use_cache, 
                                    quality=self.quality
                                )
                                
                                if img_data is not None:
                                    # Store in in-memory cache
                                    self.processed_images[path] = img_data
                                    current_chunk_processed += 1
                                    
                                    # Also try to add to queue if there's room
                                    try:
                                        if not self.image_queue.full():
                                            self.image_queue.put((path, img_data))
                                    except:
                                        pass  # Queue operations can fail, but we have the in-memory cache as backup
                        except Exception as e:
                            print(f"Error preloading image {img_path}: {e}")
                
                # Second priority: process next chunk
                elif self.next_chunk:
                    unprocessed_next = [p for p in self.next_chunk if p not in self.processed_images]
                    
                    if unprocessed_next:
                        img_path = unprocessed_next[0]
                        # Prioritize NEF files
                        if img_path.lower().endswith('.nef') or len([p for p in unprocessed_next if p.lower().endswith('.nef')]) == 0:
                            try:
                                if img_path not in self.processed_images:
                                    print(f"Preloading next chunk image: {os.path.basename(img_path)}")
                                    path, img_data = process_image(
                                        img_path,
                                        self.max_width,
                                        self.max_height,
                                        use_cache=self.use_cache, 
                                        quality=self.quality
                                    )
                                    
                                    if img_data is not None:
                                        # Store in in-memory cache
                                        self.processed_images[path] = img_data
                                        next_chunk_processed += 1
                            except Exception as e:
                                print(f"Error preloading next chunk image {img_path}: {e}")
                    else:
                        # Done with next chunk
                        if next_chunk_processed > 0:
                            print(f"Finished preloading all {next_chunk_processed} images in next chunk")
                            next_chunk_processed = 0  # Reset counter
                else:
                    # Both chunks fully processed
                    if current_chunk_processed > 0:
                        print(f"Finished preloading all {current_chunk_processed} images in current chunk")
                        current_chunk_processed = 0  # Reset counter
                        
                    # Nothing to do, sleep briefly
                    time.sleep(0.5)
        
                # Brief pause between images
                time.sleep(0.01)
        except Exception as e:
            print(f"Background processing error: {e}")


# Create a global instance of the background processor
background_processor = BackgroundProcessor(max_queue_size=50)
