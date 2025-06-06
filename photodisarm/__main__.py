import cv2
import rawpy
import numpy as np
import os
import shutil
import threading
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
from . import canvas

async def process_images(images: list, max_width: int, max_height: int):
    index: int = 0

    cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Image", max_width, max_height)
    while True:
        # Break if all images have been processed
        if index >= len(images):
            break

        imagePath = images[index]
        print(imagePath)
        _, imageData =  blurry.process_image(imagePath, 150, max_width, max_height)

        cv2.imshow("Image", imageData)
        key = cv2.waitKey(0)
        if key == 32:  # Space key
            imagePath = util.move_image_to_dir_with_date(imagePath)
            images[index] = imagePath
        elif key == 8:  # Backspace key (delete)
            image_name = os.path.basename(imagePath)
            new_path = os.path.join("Deleted", image_name)
            shutil.move(imagePath, new_path)
       
    cv2.destroyAllWindows()

def start_processing():
    input_dir = input_path.get()
    max_width = int(width_entry.get())
    max_height = int(height_entry.get())
    move_duplicates = bool(move_duplicates_entry.get())
    recursive = bool(recursive_search_entry.get())

    if not os.path.isdir(input_dir):
        messagebox.showerror("Error", "Invalid directory path!")
        return

    # Important fix: We need to collect the paths from the generators
    image_paths = []
    
    # Use the recursive function if selected, otherwise use the original
    if recursive:
        # Collect paths from all chunks returned by the generator
        for chunk in util.get_images_rec(input_dir):
            image_paths.extend(chunk)
    else:
        # Collect paths from all chunks returned by the generator
        for chunk in util.get_images(input_dir):
            image_paths.extend(chunk)
    
    print(f"Found {len(image_paths)} images")
    
    if move_duplicates:
        # Now image_paths is a list, not a generator
        image_paths = dub.add_with_progress(image_paths)
    
    # Close the main tkinter window after gathering all inputs
    root.destroy()
    
    # Process the images
    asyncio.run(process_images(image_paths, max_width, max_height))

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