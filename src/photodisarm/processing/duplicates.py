import hashlib
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox

from photodisarm.i18n.localization import localization
from photodisarm.utils.util import center_window, get_images_rec

class duplicates:
    def hash_image(image_path):
        try:
            with Image.open(image_path) as img:
                return hashlib.md5(img.tobytes()).hexdigest()
        except Exception as e:
            print(f"Error hashing {image_path}: {e}")
            return None

    def add_with_progress(image_directory_or_paths, output_dir=None):
        """
        Process images in chunks to detect and move duplicates.
        
        Args:
            image_directory_or_paths: Either a directory path or a list of image paths
            output_dir: Directory where the duplicates folder should be created
        
        Returns:
            List of non-duplicate image paths
        """
        # Get the proper language dictionary
        lang = localization.current_duplicate_texts
        
        dupSet = set()
        newList = []
        
        # Ensure the duplicates directory exists within the output directory
        duplicates_dir = os.path.join(output_dir, "duplicates") if output_dir else "duplicates"
        os.makedirs(duplicates_dir, exist_ok=True)
        
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
        
        duplicates_label = tk.Label(progress_window, text=lang["duplicates"].format(count=0), font=("Arial", 10))
        duplicates_label.pack()

        def process_images():
            nonlocal newList
            start_time = time.time()
            total_processed = 0
            total_duplicates = 0
            
            # Start the progress bar animation
            progress_bar.start()
            status_label.config(text=lang["processing"])
            
            try:
                # Fix the issue by checking if input is a string (directory path)
                if isinstance(image_directory_or_paths, str):
                    image_chunks_generator = get_images_rec(image_directory_or_paths)
                else:
                    # Create our own chunks from the list
                    def list_to_chunks(lst, n):
                        """Yield successive n-sized chunks from lst."""
                        for i in range(0, len(lst), n):
                            yield lst[i:i + min(n, len(lst) - i)]
                    
                    image_chunks_generator = list_to_chunks(image_directory_or_paths, 100)
            
                # Process images chunk by chunk
                for i, image_chunk in enumerate(image_chunks_generator):
                    # Update status
                    status_label.config(text=lang["processing_chunk"].format(chunk_num=i+1))
                    
                    # Process the chunk with ThreadPoolExecutor
                    with ThreadPoolExecutor() as executor:
                        # Create list of (path, hash) tuples, filtering out None hashes
                        hash_results = [(path, hash_val) for path, hash_val in 
                                    zip(image_chunk, executor.map(duplicates.hash_image, image_chunk))
                                    if hash_val is not None]
                        
                        # Process each image
                        for image_path, md5hash in hash_results:
                            if md5hash in dupSet:
                                # Move duplicate to duplicates directory
                                try:
                                    shutil.move(image_path, os.path.join(duplicates_dir, os.path.basename(image_path)))
                                    total_duplicates += 1
                                except Exception as e:
                                    print(f"Error moving duplicate {image_path}: {e}")
                            else:
                                dupSet.add(md5hash)
                                newList.append(image_path)
                            
                            # Update counters
                            total_processed += 1
                            
                            # Update GUI every few images to avoid slowdown
                            if total_processed % 5 == 0 or total_processed == 1:
                                # Update GUI
                                processed_label.config(text=lang["processed"].format(count=total_processed))
                                duplicates_label.config(text=lang["duplicates"].format(count=total_duplicates))
                                
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
                    lang["complete_message"].format(count=total_duplicates, directory=duplicates_dir)
                )
        
        # Run the processing in a background thread
        progress_window.after(100, process_images)
        progress_window.mainloop()
        
        return newList
