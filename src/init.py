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

# Import your other modules
import dub
import blurry
import util
import canvas

def load_next_chunk(image_paths, chunk_size, current_index, result_list, threshold, max_width, max_height):
    next_chunk = image_paths[current_index:current_index + chunk_size]
    
    # Initialize Pool here, as long as it's outside the main tkinter GUI thread
    with Pool(processes=cpu_count()) as pool:
        results = pool.starmap(blurry.process_image, [(imagePath, threshold, max_width, max_height) for imagePath in next_chunk])

    result_list.clear()
    result_list.extend(results)

def process_images(image_paths, threshold, chunk_size, max_width, max_height, move_duplicates):
    result_list = []
    current_index = 0

    load_next_chunk(image_paths, chunk_size, current_index, result_list, threshold, max_width, max_height)

    preload_thread = threading.Thread(target=load_next_chunk, args=(image_paths, chunk_size, current_index + chunk_size, result_list, threshold, max_width, max_height))
    preload_thread.start()

    delete_dir = "deleted_images"
    os.makedirs(delete_dir, exist_ok=True)

    cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Image", max_width, max_height)

    while current_index < len(image_paths):
        for idx, (resized_image, fm, text) in enumerate(result_list):
            if resized_image is None:
                continue

            image_path = image_paths[current_index + idx]
            date = util.get_image_metadata_date(image_path)
            (text_width, text_height), baseline = cv2.getTextSize(date, cv2.FONT_ITALIC, 0.8, 2)
            text_x = 10
            text_y = resized_image.shape[0] - 10
            cv2.rectangle(resized_image, (text_x - 5, text_y - text_height - baseline), (text_x + text_width + 5, text_y + 5), (255, 255, 255), -1)
            cv2.putText(resized_image, f"{date}", (text_x, text_y), cv2.FONT_ITALIC, 0.8, (0, 0, 0), 2)

            cv2.imshow("Image", resized_image)
            key = cv2.waitKeyEx(0)

            if key == 32:  # Space key
                util.move_image_to_dir_with_date(image_path)
            elif key == 8:  # Backspace key
                image_name = os.path.basename(image_path)
                new_path = os.path.join(delete_dir, image_name)
                shutil.move(image_path, new_path)
            elif key == 27:  # Esc key
                break

            if idx >= len(result_list) - 1 and current_index + chunk_size < len(image_paths):
                current_index += chunk_size
                load_next_chunk(image_paths, chunk_size, current_index, result_list, threshold, max_width, max_height)
                break

        if key == 27:
            break

    cv2.destroyAllWindows()

def start_processing():
    input_dir = input_path.get()
    threshold = float(threshold_entry.get())
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
    process_images(image_paths, threshold, chunk_size, max_width, max_height, move_duplicates)

if __name__ == "__main__":
    # Setting up the GUI
    root = tk.Tk()
    root.title("Image Processing Interface")

    # Input Directory
    input_path = tk.StringVar()
    tk.Label(root, text="Input Directory").grid(row=0, column=0, sticky=tk.W)
    tk.Entry(root, textvariable=input_path, width=50).grid(row=0, column=1)
    tk.Button(root, text="Browse", command=lambda: input_path.set(filedialog.askdirectory())).grid(row=0, column=2)

    # Threshold
    tk.Label(root, text="Threshold").grid(row=1, column=0, sticky=tk.W)
    threshold_entry = tk.Entry(root)
    threshold_entry.insert(0, "150.0")
    threshold_entry.grid(row=1, column=1)

    # Chunk Size
    tk.Label(root, text="Chunk Size").grid(row=2, column=0, sticky=tk.W)
    chunk_size_entry = tk.Entry(root)
    chunk_size_entry.insert(0, "15")
    chunk_size_entry.grid(row=2, column=1)

    # Max Width
    tk.Label(root, text="Max Width").grid(row=3, column=0, sticky=tk.W)
    width_entry = tk.Entry(root)
    width_entry.insert(0, "1720")
    width_entry.grid(row=3, column=1)

    # Max Height
    tk.Label(root, text="Max Height").grid(row=4, column=0, sticky=tk.W)
    height_entry = tk.Entry(root)
    height_entry.insert(0, "1000")
    height_entry.grid(row=4, column=1)

    # Move Duplicates Checkbox
    move_duplicates_entry = tk.IntVar()
    move_duplicates_entry.set(True)
    tk.Checkbutton(root, text="Move Duplicates", variable=move_duplicates_entry).grid(row=5, column=1)

    # Start Button
    tk.Button(root, text="Start Processing", command=start_processing).grid(row=6, column=1)

    root.mainloop()
