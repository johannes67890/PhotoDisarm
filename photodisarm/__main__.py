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
import photodisarm.dub as dub
import photodisarm.blurry as blurry
import photodisarm.util as util

# Define language dictionaries for UI text
ENGLISH = {
    "window_title": "Image Processing Interface",
    "input_dir": "Input Directory",
    "browse": "Browse",
    "threshold": "Threshold",
    "chunk_size": "Chunk Size",
    "max_width": "Max Width",
    "max_height": "Max Height",
    "delete_duplicates": "Delete Duplicates",
    "search_recursively": "Search Recursively",
    "start_processing": "Start Processing",
    "switch_lang": "Skift til dansk",  # Change to Danish
    "error": "Error",
    "invalid_dir": "Invalid directory path!",
    "done": "Done!",
    "all_processed": "All images processed!",
    "image_window": "Image",
    "loading_chunk": "Loading chunk",
    "images": "images",
    "sorted_by_date": "Sorted by date",
    "processing_image": "Processing image",
    "no_date": "*No Date Found*"
}

DANISH = {
    "window_title": "Billedbehandlingsværktøj",
    "input_dir": "Inputmappe",
    "browse": "Gennemse",
    "threshold": "Tærskelværdi",
    "chunk_size": "Gruppestørrelse",
    "max_width": "Maks. bredde",
    "max_height": "Maks. højde",
    "delete_duplicates": "Slet dubletter",
    "search_recursively": "Søg rekursivt",
    "start_processing": "Start behandling",
    "switch_lang": "Switch to English",  # Change to English
    "error": "Fejl",
    "invalid_dir": "Ugyldig mappesti!",
    "done": "Færdig!",
    "all_processed": "Alle billeder er behandlet!",
    "image_window": "Billede",
    "loading_chunk": "Indlæser gruppe",
    "images": "billeder",
    "sorted_by_date": "Sorteret efter dato",
    "processing_image": "Behandler billede",
    "no_date": "*Ingen dato fundet*"
}

# Global variable to track current language
current_language = DANISH

async def process_images(image_paths: list, max_width: int, max_height: int, chunk_size: int = 50):
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
    
    cv2.namedWindow(current_language["image_window"], cv2.WINDOW_NORMAL)
    cv2.resizeWindow(current_language["image_window"], max_width, max_height)
    
    # Process images in chunks
    while index < total_images:
        # Calculate the end index for current chunk
        chunk_end = min(index + chunk_size, total_images)
        
        # Extract current chunk of image paths
        chunk_paths = image_paths[index:chunk_end]
        
        # Sort this chunk by date
        chunk_paths = util.sort_images_by_date(chunk_paths)
        
        # Update the original list with the sorted chunk
        image_paths[index:chunk_end] = chunk_paths
        
        # Load current chunk of images
        print(f"{current_language['loading_chunk']} {index//chunk_size + 1}/{(total_images + chunk_size - 1)//chunk_size} ({chunk_end - index} {current_language['images']})")
        print(f"{current_language['sorted_by_date']}: {', '.join([os.path.basename(p) for p in chunk_paths])}")
        
        # Process the current chunk
        current_chunk_index = 0
        
        while index + current_chunk_index < chunk_end:
            current_index = index + current_chunk_index
            imagePath = image_paths[current_index]
            
            print(f"{current_language['processing_image']} {current_index + 1}/{total_images}: {imagePath}")
            _, imageData = blurry.process_image(imagePath, 150, max_width, max_height)
            
            if imageData is None:
                # Skip problematic images
                current_chunk_index += 1
                continue
                
            # Display info about current position and date
            status_image = imageData.copy()
            
            # Try to get the image date
            image_date = util.get_image_metadata_date(imagePath)
            date_info = f" - {image_date}" if image_date else current_language["no_date"]
            
            # Display position info
            cv2.putText(
                status_image, 
                f"{current_language['image_window']} {current_index + 1}/{total_images} - {date_info}",
                (10, max_height - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
            )
            
            cv2.imshow(current_language["image_window"], status_image)
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
    messagebox.showinfo(current_language["done"], current_language["all_processed"])
    cv2.destroyAllWindows()

def switch_language():
    global current_language
    
    # Toggle between English and Danish
    if current_language == ENGLISH:
        current_language = DANISH
    else:
        current_language = ENGLISH
        
    # Update all UI text
    root.title(current_language["window_title"])
    
    # Update all labels
    input_dir_label.config(text=current_language["input_dir"])
    browse_button.config(text=current_language["browse"])
    threshold_label.config(text=current_language["threshold"])
    chunk_size_label.config(text=current_language["chunk_size"])
    width_label.config(text=current_language["max_width"])
    height_label.config(text=current_language["max_height"])
    duplicates_checkbox.config(text=current_language["delete_duplicates"])
    recursive_checkbox.config(text=current_language["search_recursively"])
    start_button.config(text=current_language["start_processing"])
    language_button.config(text=current_language["switch_lang"])

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
        messagebox.showerror(current_language["error"], current_language["invalid_dir"])
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
    root.title(current_language["window_title"])
    util.center_window(root, width=550, height=400)  # Increase width to accommodate longer text

    # Configure the grid to center content horizontally
    root.columnconfigure(0, weight=3)  # More weight for the label column
    root.columnconfigure(1, weight=5)  # Input field column
    root.columnconfigure(2, weight=1)  # For buttons

    # Language Button - Move to top left corner
    language_button = tk.Button(root, text=current_language["switch_lang"], command=switch_language)
    language_button.grid(row=0, column=0, sticky="nw", padx=10, pady=10)
    
    # Give the language button a distinctive color
    language_button.config(bg="#e0e0ff")

    # Input Directory - Moved down one row
    input_path = tk.StringVar()
    input_dir_label = tk.Label(root, text=current_language["input_dir"], anchor="e", width=20)
    input_dir_label.grid(row=1, column=0, sticky="e", padx=5, pady=5)
    
    input_entry = tk.Entry(root, textvariable=input_path, width=40)
    input_entry.grid(row=1, column=1, sticky="ew", padx=5)
    input_path.set(os.getcwd())
    
    # Browse button
    browse_button = tk.Button(
        root, 
        text=current_language["browse"], 
        command=lambda: input_path.set(filedialog.askdirectory(initialdir=os.getcwd()))
    )
    browse_button.grid(row=1, column=2, sticky="w", padx=5)

    # Threshold
    threshold_label = tk.Label(root, text=current_language["threshold"], anchor="e", width=20)
    threshold_label.grid(row=2, column=0, sticky="e", padx=5, pady=5)
    
    threshold_entry = tk.Entry(root, width=10)
    threshold_entry.insert(0, "150.0")
    threshold_entry.grid(row=2, column=1, sticky="w", padx=5)

    # Chunk Size
    chunk_size_label = tk.Label(root, text=current_language["chunk_size"], anchor="e", width=20)
    chunk_size_label.grid(row=3, column=0, sticky="e", padx=5, pady=5)
    
    chunk_size_entry = tk.Entry(root, width=10)
    chunk_size_entry.insert(0, "5")
    chunk_size_entry.grid(row=3, column=1, sticky="w", padx=5)

    # Max Width
    width_label = tk.Label(root, text=current_language["max_width"], anchor="e", width=20)
    width_label.grid(row=4, column=0, sticky="e", padx=5, pady=5)
    
    width_entry = tk.Entry(root, width=10)
    width_entry.insert(0, "1720")
    width_entry.grid(row=4, column=1, sticky="w", padx=5)

    # Max Height
    height_label = tk.Label(root, text=current_language["max_height"], anchor="e", width=20)
    height_label.grid(row=5, column=0, sticky="e", padx=5, pady=5)
    
    height_entry = tk.Entry(root, width=10)
    height_entry.insert(0, "1000")
    height_entry.grid(row=5, column=1, sticky="w", padx=5)

    # Checkboxes in a new frame for better organization
    checkbox_frame = tk.Frame(root)
    checkbox_frame.grid(row=6, column=0, columnspan=3, sticky="w", padx=10, pady=10)
    
    # Move Duplicates Checkbox
    move_duplicates_entry = tk.IntVar()
    move_duplicates_entry.set(False)
    duplicates_checkbox = tk.Checkbutton(checkbox_frame, text=current_language["delete_duplicates"], variable=move_duplicates_entry)
    duplicates_checkbox.pack(anchor="w", pady=2)

    # Recursive Search Checkbox
    recursive_search_entry = tk.IntVar()
    recursive_search_entry.set(True)
    recursive_checkbox = tk.Checkbutton(checkbox_frame, text=current_language["search_recursively"], variable=recursive_search_entry)
    recursive_checkbox.pack(anchor="w", pady=2)

    # Start Button
    start_button = tk.Button(root, text=current_language["start_processing"], command=start_processing)
    start_button.grid(row=7, column=0, columnspan=3, pady=20)
    # Make the start button larger and more prominent
    start_button.config(height=2, width=20, bg="#d0f0d0", font=("Arial", 10, "bold"))

    root.mainloop()