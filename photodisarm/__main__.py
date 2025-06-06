import cv2
import numpy as np
import os
import shutil
from glob import glob
from multiprocessing import Pool, cpu_count
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import deque
import asyncio
# Import your other modules
from . import dub
from . import blurry
from . import util

async def process_images(image_paths: list, max_width: int, max_height: int, chunk_size: int = 25):
    """
    Process images in chunks to reduce memory usage.
    
    Args:
        image_paths: List of paths to images
        max_width: Maximum width for image display
        max_height: Maximum height for image display
        chunk_size: Number of images to load into memory at once
    """
    index: int = 0
    total_images = len(image_paths)
    
    cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Image", max_width, max_height)
    
    # Process images in chunks
    while index < total_images:
        # Calculate the end index for current chunk
        chunk_end = min(index + chunk_size, total_images)
        
        # Load current chunk of images
        print(f"Loading chunk {index//chunk_size + 1}/{(total_images + chunk_size - 1)//chunk_size} ({chunk_end - index} images)")
        
        # Process the current chunk
        current_chunk_index = 0
        
        while index + current_chunk_index < chunk_end:
            current_index = index + current_chunk_index
            imagePath = image_paths[current_index]
            
            print(f"Processing image {current_index + 1}/{total_images}: {imagePath}")
            _, imageData = blurry.process_image(imagePath, 150, max_width, max_height)
            
            if imageData is None:
                # Skip problematic images
                current_chunk_index += 1
                continue
                
            # Display info about current position
            status_image = imageData.copy()
            cv2.putText(
                status_image, 
                f"Image {current_index + 1}/{total_images}",
                (10, max_height - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
            )
            
            cv2.imshow("Image", status_image)
            key = cv2.waitKey(0)
            print(key)
            if key == 32:  # Space key
                new_path = util.move_image_to_dir_with_date(imagePath)
                # Update the path in the original list
                image_paths[current_index] = new_path
                current_chunk_index += 1
            elif key == 8:  # Backspace key (delete)
                os.makedirs("Deleted", exist_ok=True)
                image_name = os.path.basename(imagePath)
                new_path = os.path.join("Deleted", image_name)
                shutil.move(imagePath, new_path)
                current_chunk_index += 1
            elif key == 27 or key == -1:  # Esc key
                cv2.destroyAllWindows()
                return

            else:
                # For any other key, move to next image
                current_chunk_index += 1
        
        # Move to the next chunk
        index = chunk_end
    
    # All chunks processed
    cv2.destroyAllWindows()
    print("All images processed.")

# Update the start_processing function to pass the chunk size
def start_processing():
    input_dir = input_path.get()
    max_width = int(width_entry.get())
    max_height = int(height_entry.get())
    move_duplicates = bool(move_duplicates_entry.get())
    recursive = bool(recursive_search_entry.get())
    chunk_size = int(chunk_size_entry.get())  # Get chunk size from the UI

    # Rest of the function remains the same
    if not os.path.isdir(input_dir):
        messagebox.showerror("Error", "Invalid directory path!")
        return

    image_paths = []
    
    if recursive:
        for chunk in util.get_images_rec(input_dir):
            image_paths.extend(chunk)
    else:
        for chunk in util.get_images(input_dir):
            image_paths.extend(chunk)
    
    print(f"Found {len(image_paths)} images")
    
    if move_duplicates:
        image_paths = dub.add_with_progress(image_paths)
    
    root.destroy()
    print(f"Processing {len(image_paths)} images in chunks of {chunk_size}")
    # Pass the chunk size to process_images
    asyncio.run(process_images(image_paths, max_width, max_height, chunk_size))

if __name__ == "__main__":
   
    # Setting up the GUI
    root = tk.Tk()
    root.title("Image Processing Interface")
    util.center_window(root, width=500, height=300)  # Adjust size as needed

    # Configure the grid to center content horizontally
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)
    root.columnconfigure(2, weight=1)

    # Input Directory
    input_path = tk.StringVar()
    tk.Label(root, text="Input Directory").grid(row=0, column=0, columnspan=2, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=input_path, width=50).grid(row=0, column=1, columnspan=2, sticky="w", padx=5)
    input_path.set(os.getcwd())
    # tk.Button(root, text="Browse", command=lambda: input_path.set(filedialog.askdirectory())).grid(row=0, column=3, sticky="w", padx=5)
    tk.Button(root, text="Browse", command=lambda: input_path.set("C:/Users/johan/PhotoDisarm/pics")).grid(row=0, column=3, sticky="w", padx=5)

    # Threshold
    tk.Label(root, text="Threshold").grid(row=1, column=0, columnspan=2, sticky="e", padx=5, pady=5)
    threshold_entry = tk.Entry(root)
    threshold_entry.insert(0, "150.0")
    threshold_entry.grid(row=1, column=1, columnspan=2, sticky="w", padx=5)

    # Chunk Size
    tk.Label(root, text="Chunk Size").grid(row=2, column=0, columnspan=2, sticky="e", padx=5, pady=5)
    chunk_size_entry = tk.Entry(root)
    chunk_size_entry.insert(0, "5")
    chunk_size_entry.grid(row=2, column=1, columnspan=2, sticky="w", padx=5)

    # Max Width
    tk.Label(root, text="Max Width").grid(row=3, column=0, columnspan=2, sticky="e", padx=5, pady=5)
    width_entry = tk.Entry(root)
    width_entry.insert(0, "1720")
    width_entry.grid(row=3, column=1, columnspan=2, sticky="w", padx=5)

    # Max Height
    tk.Label(root, text="Max Height").grid(row=4, column=0, columnspan=2, sticky="e", padx=5, pady=5)
    height_entry = tk.Entry(root)
    height_entry.insert(0, "1000")
    height_entry.grid(row=4, column=1, columnspan=2, sticky="w", padx=5)

    # Move Duplicates Checkbox
    move_duplicates_entry = tk.IntVar()
    move_duplicates_entry.set(False)
    tk.Checkbutton(root, text="Delete Duplicates", variable=move_duplicates_entry).grid(row=5, column=1, columnspan=2, sticky="w", padx=5, pady=5)

    # Recursive Search Checkbox
    recursive_search_entry = tk.IntVar()
    recursive_search_entry.set(True)  # Default to non-recursive
    tk.Checkbutton(root, text="Search Recursively", variable=recursive_search_entry).grid(row=6, column=1, columnspan=2, sticky="w", padx=5, pady=25)  # Adjust grid position as needed

    # Start Button
    tk.Button(root, text="Start Processing", command=lambda: start_processing()).grid(row=7, column=1, columnspan=2, pady=10)

    root.mainloop()