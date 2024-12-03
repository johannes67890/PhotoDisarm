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

# Import your other modules
import dub
import blurry
import util
import canvas
import asyncio
async def load_next_chunk(images: list, index: int, chunk_size: int, max_width: int, max_height: int):
    next_chunk = images[index:index + chunk_size]

    with Pool(processes=cpu_count()) as pool:
        # Pass each image path as a tuple to pool.starmap()
        image = pool.starmap(blurry.process_image, [(imagePath, 150, max_width, max_height) for imagePath in next_chunk])

    return image



async def process_images(images: list, chunk_size: int, max_width: int, max_height: int, move_duplicates: bool):
    index: int = 0
    preview: bool = False
    container = []
    queue = deque(maxlen=7)

    cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Image", max_width, max_height)
    while True:
        # Break if all images have been processed
        if index >= len(images):
            break

        # if index % chunk_size == 0:
        #    container = await load_next_chunk(images, index, chunk_size, max_width, max_height)
        imagePath = images[index]
        print(imagePath)
        _, imageData =  blurry.process_image(imagePath, 150, max_width, max_height)

        cv2.imshow("Image", imageData)


        key = cv2.waitKey(0)
        print(key)
        if key == 32:  # Space key
            imagePath = util.move_image_to_dir_with_date(imagePath)
            images[index] = imagePath
        elif key == 8:  # Backspace key (delete)
            # image_name = os.path.basename(imagePath)
            # new_path = os.path.join("Deleted", image_name)
            # shutil.move(imagePath, new_path)
            print("delete Unimplemented")
        elif key == 83: # Right arrow key
            index += 1
        elif key == 81: # Left Arrow key
            if index-1 >= 0:
                index -= 1
        elif key == 27 or key == -1:  # Esc key
            cv2.destroyAllWindows()
            container.clear()
            return
        if len(queue) < queue.maxlen:
            queue.append((imagePath, imageData))
        else:
            queue.popleft()
            queue.append((imagePath, imageData))
    cv2.destroyAllWindows()

def start_processing():
    input_dir = input_path.get()
    chunk_size = int(chunk_size_entry.get())
    max_width = int(width_entry.get())
    max_height = int(height_entry.get())
    move_duplicates = bool(move_duplicates_entry.get())


    if not os.path.isdir(input_dir):
        messagebox.showerror("Error", "Invalid directory path!")
        return

    # Close the main tkinter window after gathering all inputs
    root.destroy()  # Close the window after getting the inputs
    
    image_paths = util.get_images(input_dir, move_duplicates=move_duplicates)

    # Directly call process_images on the main thread
    asyncio.run(process_images(image_paths, chunk_size, max_width, max_height, move_duplicates))

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
    tk.Button(root, text="Browse", command=lambda: input_path.set("/home/johannes/repos/PhotoDisarm/pics")).grid(row=0, column=3, sticky="w", padx=5)

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
    move_duplicates_entry.set(True)
    tk.Checkbutton(root, text="Move Duplicates", variable=move_duplicates_entry).grid(row=5, column=1, columnspan=2, sticky="w", padx=5, pady=5)

    # Start Button
    tk.Button(root, text="Start Processing", command=lambda: start_processing()).grid(row=6, column=1, columnspan=2, pady=10)

    root.mainloop()