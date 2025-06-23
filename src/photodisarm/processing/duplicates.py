"""
Duplicate detection module for PhotoDisarm

Provides functionality to detect and handle duplicate images.
"""
import hashlib
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Tuple, Set, Any, Callable
import threading

from photodisarm.i18n.localization import localization


class DuplicateDetector:
    """
    Detects and manages duplicate images based on content hashing
    """
    
    def __init__(self):
        """Initialize the duplicate detector"""
        self.file_hashes: Dict[str, str] = {}
        self.duplicate_count = 0
        self.progress_window = None
        self.progress_bar = None
        self.status_label = None
        self.time_label = None
        self.processed_label = None
        self.duplicates_label = None
        self._stop_requested = False
        self._lock = threading.Lock()
    
    def _compute_image_hash(self, image_path: str) -> str:
        """
        Compute a hash for an image file
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Hash string representing the image content
        """
        try:
            with Image.open(image_path) as img:
                # Resize for faster and more reliable comparison
                img = img.resize((64, 64))
                # Convert to grayscale
                img = img.convert("L")
                # Get pixel data
                pixels = list(img.getdata())
                # Compute hash of pixel data
                return hashlib.md5(str(pixels).encode()).hexdigest()
        except Exception:
            # Fall back to file content hash if image can't be processed
            try:
                with open(image_path, "rb") as f:
                    return hashlib.md5(f.read()).hexdigest()
            except Exception:
                # If both methods fail, return a unique string based on path
                return hashlib.md5(image_path.encode()).hexdigest()
    
    def _process_chunk(self, chunk: List[str], duplicates_dir: str) -> Tuple[int, int]:
        """
        Process a chunk of images to detect duplicates
        
        Args:
            chunk: List of image paths to process
            duplicates_dir: Directory to move duplicates to
            
        Returns:
            Tuple of (processed_count, duplicates_found)
        """
        duplicates_found = 0
        processed = 0
        
        for image_path in chunk:
            if self._stop_requested:
                break
                
            if not os.path.exists(image_path):
                continue
                
            # Calculate hash for the current image
            image_hash = self._compute_image_hash(image_path)
            processed += 1
            
            # Check if we've already seen this hash
            with self._lock:
                if image_hash in self.file_hashes:
                    # This is a duplicate
                    duplicates_found += 1
                    
                    # Move to duplicates directory
                    os.makedirs(duplicates_dir, exist_ok=True)
                    filename = os.path.basename(image_path)
                    base_name, ext = os.path.splitext(filename)
                    
                    # Handle duplicate filenames
                    counter = 1
                    new_path = os.path.join(duplicates_dir, filename)
                    while os.path.exists(new_path):
                        new_path = os.path.join(duplicates_dir, f"{base_name}_{counter}{ext}")
                        counter += 1
                    
                    # Move the duplicate file
                    shutil.move(image_path, new_path)
                else:
                    # New unique image, add to our hash dictionary
                    self.file_hashes[image_hash] = image_path
        
        return processed, duplicates_found
    
    def detect_duplicates(self, image_paths: List[str], output_dir: str) -> List[str]:
        """
        Detect duplicate images and move them to a specified directory
        
        Args:
            image_paths: List of paths to images
            output_dir: Base output directory
            
        Returns:
            List of non-duplicate image paths
        """
        self._stop_requested = False
        self.duplicate_count = 0
        self.file_hashes.clear()
        
        # Create the duplicates directory
        duplicates_dir = os.path.join(output_dir, "duplicates")
        os.makedirs(duplicates_dir, exist_ok=True)
        
        # Create progress window
        self._create_progress_window()
        
        # Start the processing thread
        thread = threading.Thread(
            target=self._process_duplicates_thread,
            args=(image_paths, duplicates_dir),
            daemon=True
        )
        thread.start()
        
        # Start the UI update loop
        self._update_progress_ui(thread)
        
        # Return the filtered list (without duplicates)
        return [path for path in image_paths if os.path.exists(path)]
    
    def _process_duplicates_thread(self, image_paths: List[str], duplicates_dir: str) -> None:
        """
        Thread function to process duplicates
        
        Args:
            image_paths: List of image paths
            duplicates_dir: Directory to move duplicates to
        """
        start_time = time.time()
        total_processed = 0
        
        # Process images in chunks for better UI responsiveness
        chunk_size = 20
        num_chunks = (len(image_paths) + chunk_size - 1) // chunk_size
        
        with ThreadPoolExecutor(max_workers=max(1, os.cpu_count() - 1)) as executor:
            for i in range(0, len(image_paths), chunk_size):
                if self._stop_requested:
                    break
                
                # Update UI to show which chunk we're processing
                chunk_num = i // chunk_size + 1
                text = localization.current_duplicate_texts["processing_chunk"].format(chunk_num=f"{chunk_num}/{num_chunks}")
                if self.status_label and self.status_label.winfo_exists():
                    self.status_label.config(text=text)
                
                # Process the chunk
                chunk = image_paths[i:i + chunk_size]
                processed, found = self._process_chunk(chunk, duplicates_dir)
                total_processed += processed
                self.duplicate_count += found
                
                # Update progress
                progress = min(100, int(100 * (i + len(chunk)) / len(image_paths)))
                if self.progress_bar and self.progress_bar.winfo_exists():
                    self.progress_bar["value"] = progress
    
    def _create_progress_window(self) -> None:
        """Create and configure the progress window"""
        self.progress_window = tk.Toplevel()
        self.progress_window.title(localization.current_duplicate_texts["title"])
        self.progress_window.geometry("400x200")
        
        # Center the window
        self.progress_window.update_idletasks()
        width = self.progress_window.winfo_width()
        height = self.progress_window.winfo_height()
        x = (self.progress_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.progress_window.winfo_screenheight() // 2) - (height // 2)
        self.progress_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Make window stay on top
        self.progress_window.attributes("-topmost", True)
        
        # Status label
        self.status_label = ttk.Label(self.progress_window, 
                                      text=localization.current_duplicate_texts["checking"])
        self.status_label.pack(pady=(20, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_window, orient="horizontal", length=350, mode="determinate"
        )
        self.progress_bar.pack(pady=5)
        
        # Stats labels
        stats_frame = ttk.Frame(self.progress_window)
        stats_frame.pack(fill="x", expand=True, pady=5)
        
        # Time label
        self.time_label = ttk.Label(stats_frame, text="")
        self.time_label.pack(pady=2)
        
        # Processed label
        self.processed_label = ttk.Label(stats_frame, text="")
        self.processed_label.pack(pady=2)
        
        # Duplicates label
        self.duplicates_label = ttk.Label(stats_frame, text="")
        self.duplicates_label.pack(pady=2)
    
    def _update_progress_ui(self, worker_thread: threading.Thread) -> None:
        """
        Update the progress window UI
        
        Args:
            worker_thread: The thread processing the duplicates
        """
        start_time = time.time()
        
        # Check if the window still exists
        if self.progress_window and self.progress_window.winfo_exists():
            # Update stats
            elapsed = time.time() - start_time
            
            # Update labels
            if self.time_label and self.time_label.winfo_exists():
                self.time_label.config(
                    text=localization.current_duplicate_texts["elapsed_time"].format(seconds=int(elapsed))
                )
            
            if self.processed_label and self.processed_label.winfo_exists():
                processed_count = len(self.file_hashes)
                self.processed_label.config(
                    text=localization.current_duplicate_texts["processed"].format(count=processed_count)
                )
            
            if self.duplicates_label and self.duplicates_label.winfo_exists():
                self.duplicates_label.config(
                    text=localization.current_duplicate_texts["duplicates"].format(count=self.duplicate_count)
                )
            
            # Schedule the next update
            if worker_thread.is_alive():
                self.progress_window.after(100, lambda: self._update_progress_ui(worker_thread))
            else:
                # Processing finished
                self._show_completion_message()
        elif worker_thread.is_alive():
            # Window was closed but thread is still running
            self._stop_requested = True
            worker_thread.join(timeout=1.0)  # Give it a moment to stop
    
    def _show_completion_message(self) -> None:
        """Show completion message and close the progress window"""
        if self.progress_window and self.progress_window.winfo_exists():
            # Get the duplicates directory path from the window title
            duplicates_dir = "duplicates"  # Default fallback
            
            # Show completion message
            messagebox.showinfo(
                localization.current_duplicate_texts["complete"],
                localization.current_duplicate_texts["complete_message"].format(
                    count=self.duplicate_count,
                    directory=duplicates_dir
                )
            )
            
            # Close the progress window
            self.progress_window.destroy()


# Helper function for external use
def find_duplicates(image_paths: List[str], output_dir: str) -> List[str]:
    """
    Find and move duplicate images to the duplicates directory
    
    Args:
        image_paths: List of paths to images
        output_dir: Base output directory
        
    Returns:
        List of non-duplicate image paths
    """
    detector = DuplicateDetector()
    return detector.detect_duplicates(image_paths, output_dir)
