import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import rawpy
import numpy as np

from photodisarm.i18n.localization import localization
from photodisarm.utils.util import center_window, get_images_rec


class CorruptDetector:
    """
    Class for detecting and handling corrupt image files.
    
    This class recursively scans through directories to find image files
    that cannot be processed, and moves them to a 'corrupted' folder.
    """
    
    @staticmethod
    def test_image_integrity(image_path):
        """
        Test if an image file can be opened and processed.
        
        Args:
            image_path: Path to the image file to test
            
        Returns:
            True if image is valid, False if corrupt
        """
        try:
            # Test based on file extension
            if image_path.lower().endswith('.nef'):
                # Test NEF files with rawpy
                with rawpy.imread(image_path) as raw:
                    # Try to process a small preview to test integrity
                    rgb_image = raw.postprocess(use_camera_wb=True, half_size=True)
                    # If we get here, the file is readable
                    return True
            else:
                # Test regular image files with PIL and OpenCV
                # First try PIL
                with Image.open(image_path) as img:
                    # Try to load the image data
                    img.load()
                    # Also verify it's a valid image format
                    img.verify()
                
                # Then try OpenCV method for additional verification
                with open(image_path, 'rb') as f:
                    file_bytes = np.frombuffer(f.read(), np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                
                # If image is None, it's corrupt
                if image is None:
                    return False
                    
                return True
                
        except Exception as e:
            print(f"Corrupt image detected {image_path}: {e}")
            return False

    @staticmethod
    def scan_for_corrupt_images(image_directory_or_paths, output_dir=None):
        """
        Scan for corrupt images and move them to a 'corrupted' folder.
        
        Args:
            image_directory_or_paths: Either a directory path or a list of image paths
            output_dir: Directory where the corrupted folder should be created
        
        Returns:
            List of valid (non-corrupt) image paths
        """
        # Get the proper language dictionary - use corruption texts
        lang = localization.current_corruption_texts
        
        valid_images = []
        corrupt_count = 0
        
        # Ensure the corrupted directory exists within the output directory
        corrupted_dir = os.path.join(output_dir, "corrupted") if output_dir else "corrupted"
        os.makedirs(corrupted_dir, exist_ok=True)
        
        # Configure the GUI progress bar
        progress_window = tk.Tk()
        progress_window.title(lang["title"])
        center_window(progress_window, 500, 250)
        
        label = tk.Label(progress_window, text=lang["checking"], font=("Arial", 12))
        label.pack(pady=10)
        
        # Configure a larger progress bar style
        style = ttk.Style(progress_window)
        style.configure(
            'Large.Horizontal.TProgressbar',
            thickness=30
        )
        
        # Create a progress bar (indeterminate mode)
        progress_bar = ttk.Progressbar(
            progress_window, 
            mode="indeterminate",
            style='Large.Horizontal.TProgressbar'
        )
        progress_bar.pack(fill='x', padx=40, pady=20)
        
        # Create status labels
        status_label = tk.Label(progress_window, text=lang["scanning"], font=("Arial", 10))
        status_label.pack()
        
        # Labels for elapsed time
        elapsed_time_label = tk.Label(progress_window, text=lang["elapsed_time"].format(seconds=0), font=("Arial", 10))
        elapsed_time_label.pack()
        
        # Stats labels
        processed_label = tk.Label(progress_window, text=lang["processed"].format(count=0), font=("Arial", 10))
        processed_label.pack()
        
        corrupted_label = tk.Label(progress_window, text=lang["corrupted"].format(count=0), font=("Arial", 10))
        corrupted_label.pack()

        def process_images():
            nonlocal valid_images, corrupt_count
            start_time = time.time()
            total_processed = 0
            
            # Start the progress bar animation
            progress_bar.start()
            status_label.config(text=lang["processing"])
            
            try:
                # Handle both directory paths and lists of image paths
                if isinstance(image_directory_or_paths, str):
                    image_chunks_generator = get_images_rec(image_directory_or_paths)
                else:
                    # Create our own chunks from the list
                    def list_to_chunks(lst, n):
                        """Yield successive n-sized chunks from lst."""
                        for i in range(0, len(lst), n):
                            yield lst[i:i + min(n, len(lst) - i)]
                    
                    image_chunks_generator = list_to_chunks(image_directory_or_paths, 50)
            
                # Process images chunk by chunk
                for i, image_chunk in enumerate(image_chunks_generator):
                    # Update status
                    status_label.config(text=lang["processing_chunk"].format(chunk_num=i+1))
                    
                    # Process the chunk with ThreadPoolExecutor
                    with ThreadPoolExecutor() as executor:
                        # Create list of (path, is_valid) tuples
                        integrity_results = list(zip(
                            image_chunk, 
                            executor.map(CorruptDetector.test_image_integrity, image_chunk)
                        ))
                        
                        # Process each image
                        for image_path, is_valid in integrity_results:
                            if not is_valid:
                                # Move corrupt image to corrupted directory
                                try:
                                    # Create unique filename if file already exists in corrupted folder
                                    base_name = os.path.basename(image_path)
                                    dest_path = os.path.join(corrupted_dir, base_name)
                                    
                                    # Handle filename conflicts
                                    if os.path.exists(dest_path):
                                        name, ext = os.path.splitext(base_name)
                                        counter = 1
                                        while os.path.exists(dest_path):
                                            dest_path = os.path.join(corrupted_dir, f"{name}_{counter}{ext}")
                                            counter += 1
                                    
                                    shutil.move(image_path, dest_path)
                                    corrupt_count += 1
                                    print(f"Moved corrupt image: {image_path} -> {dest_path}")
                                except Exception as e:
                                    print(f"Error moving corrupt image {image_path}: {e}")
                            else:
                                valid_images.append(image_path)
                            
                            # Update counters
                            total_processed += 1
                            
                            # Update GUI every few images to avoid slowdown
                            if total_processed % 5 == 0 or total_processed == 1:
                                # Update GUI
                                processed_label.config(text=lang["processed"].format(count=total_processed))
                                corrupted_label.config(text=lang["corrupted"].format(count=corrupt_count))
                                
                                # Calculate elapsed time
                                elapsed_time = time.time() - start_time
                                elapsed_time_label.config(text=lang["elapsed_time"].format(seconds=int(elapsed_time)))
                                
                                # Update window to prevent freezing
                                progress_window.update_idletasks()
                    
            finally:
                # Processing complete
                progress_bar.stop()
                progress_window.destroy()
                messagebox.showinfo(
                    lang["complete"], 
                    lang["complete_message"].format(count=corrupt_count, directory=corrupted_dir)
                )
        
        # Run the processing in a background thread
        progress_window.after(100, process_images)
        progress_window.mainloop()
        
        return valid_images

    @staticmethod
    def scan_directory_for_corrupt_images(directory_path, output_dir=None):
        """
        Convenience method to scan a directory for corrupt images.
        
        Args:
            directory_path: Path to directory to scan
            output_dir: Directory where the corrupted folder should be created
        
        Returns:
            List of valid (non-corrupt) image paths
        """
        return CorruptDetector.scan_for_corrupt_images(directory_path, output_dir)

    @staticmethod
    def scan_image_list_for_corrupt_images(image_paths, output_dir=None):
        """
        Convenience method to scan a list of image paths for corrupt images.
        
        Args:
            image_paths: List of image paths to check
            output_dir: Directory where the corrupted folder should be created
        
        Returns:
            List of valid (non-corrupt) image paths
        """
        return CorruptDetector.scan_for_corrupt_images(image_paths, output_dir)


# For backwards compatibility and simpler usage
def detect_and_move_corrupt_images(image_directory_or_paths, output_dir=None):
    """
    Detect and move corrupt images. This is the main function users should call.
    
    Args:
        image_directory_or_paths: Either a directory path or a list of image paths
        output_dir: Directory where the corrupted folder should be created
    
    Returns:
        List of valid (non-corrupt) image paths
    """
    return CorruptDetector.scan_for_corrupt_images(image_directory_or_paths, output_dir)
