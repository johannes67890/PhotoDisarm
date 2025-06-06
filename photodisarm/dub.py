import hashlib
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox
from . import util

def hash_image(image_path):
    with Image.open(image_path) as img:
        return hashlib.md5(img.tobytes()).hexdigest()

def add_with_progress(image_paths: list):
    dupSet = set()
    newList = []
    
    # Ensure the duplicates directory exists
    duplicates_dir = "duplicates"
    os.makedirs(duplicates_dir, exist_ok=True)
    
    # Configure the GUI progress bar
    progress_window = tk.Tk()
    progress_window.title("Processing Duplicates")
    util.center_window(progress_window, 500, 250)  # Center the window
    
    label = tk.Label(progress_window, text="Checking & moving duplicates...", font=("Arial", 12))
    label.pack(pady=10)
    
    # Configure a larger progress bar style
    style = ttk.Style(progress_window)
    style.configure(
        'Large.Horizontal.TProgressbar',
        thickness=30  # Increase thickness
    )
    
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=len(image_paths), style='Large.Horizontal.TProgressbar')
    progress_bar.pack(fill='x', padx=40, pady=20)  # Add more padding to make the bar stand out
    
    # Labels for elapsed time and estimated time remaining
    elapsed_time_label = tk.Label(progress_window, text="Elapsed Time: 0s", font=("Arial", 10))
    elapsed_time_label.pack()
    
    estimated_time_label = tk.Label(progress_window, text="Estimated Time Remaining: Calculating...", font=("Arial", 10))
    estimated_time_label.pack()

    def process_images():
        start_time = time.time()
        
        with ThreadPoolExecutor() as executor:
            for i, (image_path, md5hash) in enumerate(zip(image_paths, executor.map(hash_image, image_paths))):
                if md5hash in dupSet:
                    shutil.move(image_path, duplicates_dir)
                else:
                    dupSet.add(md5hash)
                    newList.append(image_path)
                
                # Update progress
                progress_var.set(i + 1)
                progress_window.update_idletasks()
                
                # Calculate elapsed time and estimate remaining time
                elapsed_time = time.time() - start_time
                elapsed_time_label.config(text=f"Elapsed Time: {int(elapsed_time)}s")
                
                if i > 0:  # Avoid division by zero
                    avg_time_per_file = elapsed_time / (i + 1)
                    estimated_time_remaining = avg_time_per_file * (len(image_paths) - i - 1)
                    estimated_time_label.config(text=f"Estimated Time Remaining: {int(estimated_time_remaining)}s")

        progress_window.destroy()
        messagebox.showinfo("Processing Complete", f"{len(image_paths) - len(newList)} duplicates found and moved to {duplicates_dir}")

    # Run the processing in a background thread
    progress_window.after(100, process_images)
    progress_window.mainloop()
    
    return newList
