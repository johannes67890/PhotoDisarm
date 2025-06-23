try:
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
    import threading
    import queue
    import time
    # Import your other modules
    import photodisarm.dub as dub
    import photodisarm.canvas as canvas
    import photodisarm.blurry as blurry
    import photodisarm.util as util

    # Define language dictionaries for UI text    
    ENGLISH = {
        "window_title": "Image Processing Interface",
        "input_dir": "Input Directory",
        "output_dir": "Output Directory",
        "browse": "Browse",
        "threshold": "Threshold",
        "chunk_size": "Chunk Size",
        "max_width": "Max Width",
        "max_height": "Max Height",
        "delete_duplicates": "Delete Duplicates",
        "search_recursively": "Search Recursively",
        "start_processing": "Start Processing",
        "switch_lang": "Skift til dansk",  
        "error": "Error",
        "invalid_dir": "Invalid directory path!",
        "done": "Done!",
        "all_processed": "All images processed!",
        "image_window": "Image",
        "loading_chunk": "Loading chunk",
        "images": "images",
        "sorted_by_date": "Sorted by date",
        "processing_image": "Processing image",
        "no_date": "*No Date Found*",
        "keybindings": "Space: Save | Backspace: Delete | ← : Back | Any key: Skip",
        "use_cache": "Use Cache (Faster)",        "image_quality": "Image Quality:",
        "quality_low": "Low (Fast)",
        "quality_normal": "Normal",
        "quality_high": "High (Best)",
        "preloading": "Preloading next images in background...",
        "loaded_from_cache": "Image loaded from preload cache"
    }

    DANISH = {
        "window_title": "Billedbehandlingsværktøj",
        "input_dir": "Inputmappe",
        "output_dir": "Outputmappe",
        "browse": "Gennemse",
        "threshold": "Tærskelværdi",
        "chunk_size": "Gruppestørrelse",
        "max_width": "Maks. bredde",
        "max_height": "Maks. højde",
        "delete_duplicates": "Slet dubletter",
        "search_recursively": "Søg rekursivt",
        "start_processing": "Start behandling",
        "switch_lang": "Switch to English",  
        "error": "Fejl",
        "invalid_dir": "Ugyldig mappesti!",
        "done": "Færdig!",
        "all_processed": "Alle billeder er behandlet!",
        "image_window": "Billede",
        "loading_chunk": "Indlæser gruppe",
        "images": "billeder",
        "sorted_by_date": "Sorteret efter dato",
        "processing_image": "Behandler billede",
        "no_date": "*Ingen dato fundet*",
        "keybindings": "Mellemrum: Gem | Backspace: Slet | ← : Tilbage | Enhver tast: Spring over"
    }

    # Global variable to track current language
    current_language = DANISH

    async def process_images(image_paths: list, max_width: int, max_height: int, chunk_size: int = 50, output_dir: str = None, use_cache: bool = True, quality: str = 'normal'):
        """
        Process images in chunks to reduce memory usage.
        
        Args:
            image_paths: List of paths to images
            max_width: Maximum width for image display
            max_height: Maximum height for image display
            chunk_size: Number of images to load into memory at once
            output_dir: Directory for organized output files
        """
        index: int = 0
        total_images = len(image_paths)
        # Use deque with maxlen=10 to automatically limit history size
        history = deque(maxlen=10)
        if "status_saved" not in current_language:
            ENGLISH["status_saved"] = "Saved"
            ENGLISH["status_deleted"] = "Deleted"
            ENGLISH["status_skipped"] = ""
            ENGLISH["status_history"] = "History: {count}/10"
            
            DANISH["status_saved"] = "Gemt"
            DANISH["status_deleted"] = "Slettet"
            DANISH["status_skipped"] = ""
            DANISH["status_history"] = "Historik: {count}/10"
            

        # Helper function to determine image status based on path
        def get_image_status(img_path):
            if output_dir and output_dir in img_path and "Deleted" not in img_path:
                return current_language["status_saved"]
            elif "Deleted" in img_path:
                return current_language["status_deleted"]
            else:
                return current_language["status_skipped"]

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
              # Start background processor for this chunk and prepare for next chunk
            background_processor.start(
                chunk_paths,                   # Current chunk paths
                0,                            # Start at beginning of chunk
                max_width,
                max_height,
                use_cache,
                quality,
                chunk_size,                  # Pass chunk size
                image_paths,                 # Pass all image paths for next chunk calculation
                index // chunk_size          # Current chunk index
            )
            
            # Process the current chunk
            current_chunk_index = 0
            
            while index + current_chunk_index < chunk_end:                
                current_index = index + current_chunk_index
                imagePath = image_paths[current_index]
                print(f"{current_language['processing_image']} {current_index + 1}/{total_images}: {imagePath}")
                
                # Update background processor's current index for accurate prefetching
                background_processor.current_index = current_chunk_index
                
                # Get image from background processor (it will process immediately if not preloaded)
                start_time = time.time()
                _, imageData = background_processor.get_image(imagePath)
                load_time = time.time() - start_time
                
                if load_time < 0.1:
                    print(f"Image loaded instantly from preload cache ({load_time:.3f}s)")
                else:
                    print(f"Image processed in {load_time:.3f}s")
                
                if imageData is None:
                    # Skip problematic images
                    current_chunk_index += 1
                    continue
                  
                # Display info about current position and date
                status_image = imageData.copy()
                
                # Try to get the image date
                image_date = util.get_image_metadata_date(imagePath)
                date_info = f"{image_date}" if image_date else current_language["no_date"]
                
                # Display position info in bottom left corner using custom UTF-8 text function
                position_text = f"{current_language['image_window']} {current_index + 1}/{total_images}"
                status_image = canvas.put_text_utf8(
                    status_image,
                    position_text,
                    position=(10, max_height - 30),
                    font_size=18, 
                    color=(255, 255, 255),
                    thickness=2,
                    with_background=True  # Add semi-transparent background
                )
                
                # Display keybindings in bottom middle
                keybinding_text = current_language["keybindings"]
                # Calculate the center position (roughly)
                text_width = len(keybinding_text) * 7  # Rough estimate for font size 18
                center_x = (max_width - text_width) // 2
                status_image = canvas.put_text_utf8(
                    status_image,
                    keybinding_text,
                    position=(center_x, max_height - 30),
                    font_size=18,
                    color=(255, 255, 255),  # Yellow for better visibility
                    thickness=2,
                    with_background=True  # Add semi-transparent background
                )
                
                # Add history counter in top left when there's history
                current_status = get_image_status(imagePath)
                if current_status:
                    # Use different colors based on status
                    if current_status == current_language["status_saved"]:
                        status_color = (0, 255, 0)  # Green for saved
                    elif current_status == current_language["status_deleted"]:
                        status_color = (0, 0, 255)  # Red for deleted
                    else:
                        status_color = (255, 255, 255)  # Yellow for skipped
                    
                    status_image = canvas.put_text_utf8(
                        status_image,
                        current_status,
                        position=(max_width - 150, 30),
                        font_size=16,
                        color=status_color,
                        thickness=2,
                        with_background=True
                    )

                # Display date info in bottom right corner
                status_image = canvas.put_text_utf8(
                    status_image,
                    date_info,
                    position=(max_width - len(date_info) * 10 - 20, max_height - 30),
                    font_size=18,
                    color=(255, 255, 255),
                    thickness=2,
                    with_background=True  # Add semi-transparent background
                )
            
            
                cv2.imshow(current_language["image_window"], status_image)
                key = cv2.waitKeyEx(0)
                print(key)
                
                if key in (81, 2424832, 37, 65361):  # Left arrow key codes
                    if len(history) > 0:  # Only go back if history isn't empty
                        prev_original_path = history.pop()
                        
                        # Update the current position to show the previous image
                        # We need to find the index of the previous image in image_paths
                        try:
                            prev_index = image_paths.index(prev_original_path)
                            # Adjust chunk indices if necessary
                            if prev_index < index:
                                # Need to go back to previous chunk
                                new_chunk_start = (prev_index // chunk_size) * chunk_size
                                index = new_chunk_start
                                current_chunk_index = prev_index - new_chunk_start
                            else:
                                # Same chunk
                                current_chunk_index = prev_index - index
                        except ValueError:
                            # Image not found in list, just go back one
                            if current_chunk_index > 0:
                                current_chunk_index -= 1
                            elif index > 0:
                                index -= chunk_size
                                current_chunk_index = chunk_size - 1
                    else:
                        print("History limit reached, cannot go back further")
                    
                    # Skip the rest of the processing for this loop
                    continue
                    
                # Store current image in history before processing action
                if key == 32:  # Space key
                    history.append(imagePath)
                    new_path = util.move_image_to_dir_with_date(imagePath, output_dir)
                    # Update the path in the original list
                    image_paths[current_index] = new_path
                    current_chunk_index += 1
                elif key == 8:  # Backspace key (delete)
                    history.append(imagePath)
                    deleted_dir = os.path.join(output_dir, "Deleted") if output_dir else "Deleted"
                    os.makedirs(deleted_dir, exist_ok=True)
                    image_name = os.path.basename(imagePath)
                    new_path = os.path.join(deleted_dir, image_name)
                    shutil.move(imagePath, new_path)
                    image_paths[current_index] = new_path
                    current_chunk_index += 1                
                elif key == 27 or key == -1:  # Esc key
                    background_processor.stop()  # Stop background processing
                    cv2.destroyAllWindows()
                    return
                else:
                    # For any other key, store in history as skipped and move to next image
                    history.append(imagePath)
                    current_chunk_index += 1
            
            # Move to the next chunk
            index = chunk_end
          # All chunks processed
        background_processor.stop()  # Stop background processing
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
        output_dir_label.config(text=current_language["output_dir"])  # Add this line
        browse_button.config(text=current_language["browse"])
        output_browse_button.config(text=current_language["browse"])  # Add this line
        threshold_label.config(text=current_language["threshold"])
        chunk_size_label.config(text=current_language["chunk_size"])
        width_label.config(text=current_language["max_width"])
        height_label.config(text=current_language["max_height"])
        duplicates_checkbox.config(text=current_language["delete_duplicates"])
        recursive_checkbox.config(text=current_language["search_recursively"])
        start_button.config(text=current_language["start_processing"])
        language_button.config(text=current_language["switch_lang"])    # Update the start_processing function to pass the chunk size and quality options
    def start_processing():
        input_dir = input_path.get()
        output_dir = output_path.get()
        max_width = int(width_entry.get())
        max_height = int(height_entry.get())
        move_duplicates = bool(move_duplicates_entry.get())
        recursive = bool(recursive_search_entry.get())
        chunk_size = int(chunk_size_entry.get())
        use_cache = bool(use_cache_entry.get() if 'use_cache_entry' in globals() else True)
        quality = quality_var.get() if 'quality_var' in globals() else 'normal'

        # Rest of the function remains the same
        if not os.path.isdir(input_dir):
            messagebox.showerror(current_language["error"], current_language["invalid_dir"])
            return

        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        image_paths = []
        
        if recursive:
            for chunk in util.get_images_rec(input_dir):
                image_paths.extend(chunk)
        else:
            for chunk in util.get_images(input_dir):
                image_paths.extend(chunk)
        
        print(f"Found {len(image_paths)} images")
        
        if move_duplicates:
            # Pass the output directory to add_with_progress
            image_paths = dub.add_with_progress(image_paths, output_dir)
            
        print(f"Processing {len(image_paths)} images in chunks of {chunk_size}")
        print(f"Image quality: {quality}, Cache enabled: {use_cache}")
        # Pass all parameters to process_images
        asyncio.run(process_images(image_paths, max_width, max_height, chunk_size, output_dir, use_cache, quality))

    # Background processing class to preload NEF files    class BackgroundProcessor:
    class BackgroundProcessor:
        def __init__(self, max_queue_size=50):  # Increased queue size to handle full chunks
            self.image_queue = queue.Queue(maxsize=max_queue_size)
            self.processing_thread = None
            self.running = False
            self.current_chunk = []
            self.next_chunk = []
            self.current_index = 0
            self.chunk_size = 25  # Default chunk size
            self.max_width = 1000
            self.max_height = 800
            self.use_cache = True
            self.quality = 'normal'
            self.processed_images = {}  # In-memory cache for current session
        def start(self, image_paths, current_index, max_width, max_height, use_cache=True, quality='normal', chunk_size=25, all_paths=None, current_chunk_idx=0):
            """Start background processing thread with the given parameters"""
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
            self.processed_images = {path: img for path, img in self.processed_images.items() 
                                   if path in self.current_chunk or path in self.next_chunk}
            
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
            
        def stop(self):
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
        def get_image(self, image_path):
            """Get a processed image either from the cache, queue or by processing it now"""
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
            path, img_data = blurry.process_image(
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
        def _process_images(self):
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
                                    path, img_data = blurry.process_image(
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
                                        path, img_data = blurry.process_image(
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
                print(f"Background processing error: {e}")    # Create a global instance of the background processor
    background_processor = BackgroundProcessor(max_queue_size=50)

    if __name__ == "__main__":
    
        # Setting up the GUI
        root = tk.Tk()
        root.title(current_language["window_title"])
        util.center_window(root, width=500, height=450)  # Increase width to accommodate longer text

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

        # Add Output Directory - Using the next row
        output_path = tk.StringVar()
        output_dir_label = tk.Label(root, text=current_language["output_dir"], anchor="e", width=20)
        output_dir_label.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        
        output_entry = tk.Entry(root, textvariable=output_path, width=40)
        output_entry.grid(row=2, column=1, sticky="ew", padx=5)
        output_path.set(os.path.join(os.getcwd(), "output"))  # Default to 'output' subfolder
        
        # Output Browse button
        output_browse_button = tk.Button(
            root, 
            text=current_language["browse"], 
            command=lambda: output_path.set(filedialog.askdirectory(initialdir=output_path.get()))
        )
        output_browse_button.grid(row=2, column=2, sticky="w", padx=5)

        # Threshold
        threshold_label = tk.Label(root, text=current_language["threshold"], anchor="e", width=20)
        threshold_label.grid(row=3, column=0, sticky="e", padx=5, pady=5)
        
        threshold_entry = tk.Entry(root, width=10)
        threshold_entry.insert(0, "150.0")
        threshold_entry.grid(row=3, column=1, sticky="w", padx=5)

        # Chunk Size
        chunk_size_label = tk.Label(root, text=current_language["chunk_size"], anchor="e", width=20)
        chunk_size_label.grid(row=4, column=0, sticky="e", padx=5, pady=5)
        
        chunk_size_entry = tk.Entry(root, width=10)
        chunk_size_entry.insert(0, "100")
        chunk_size_entry.grid(row=4, column=1, sticky="w", padx=5)

        # Max Width
        width_label = tk.Label(root, text=current_language["max_width"], anchor="e", width=20)
        width_label.grid(row=5, column=0, sticky="e", padx=5, pady=5)
        
        width_entry = tk.Entry(root, width=10)
        width_entry.insert(0, "1720")
        width_entry.grid(row=5, column=1, sticky="w", padx=5)

        # Max Height
        height_label = tk.Label(root, text=current_language["max_height"], anchor="e", width=20)
        height_label.grid(row=6, column=0, sticky="e", padx=5, pady=5)
        
        height_entry = tk.Entry(root, width=10)
        height_entry.insert(0, "1000")
        height_entry.grid(row=6, column=1, sticky="w", padx=5)

        # Checkboxes in a new frame for better organization
        checkbox_frame = tk.Frame(root)
        checkbox_frame.grid(row=7, column=0, columnspan=3, sticky="w", padx=10, pady=10)
        
        # Move Duplicates Checkbox
        move_duplicates_entry = tk.IntVar()
        move_duplicates_entry.set(False)
        duplicates_checkbox = tk.Checkbutton(checkbox_frame, text=current_language["delete_duplicates"], variable=move_duplicates_entry)
        duplicates_checkbox.pack(anchor="w", pady=2)        # Recursive Search Checkbox
        recursive_search_entry = tk.IntVar()
        recursive_search_entry.set(True)
        recursive_checkbox = tk.Checkbutton(checkbox_frame, text=current_language["search_recursively"], variable=recursive_search_entry)
        recursive_checkbox.pack(anchor="w", pady=2)
          # Add "Use Cache" checkbox - New feature for NEF optimization
        use_cache_entry = tk.IntVar()
        use_cache_entry.set(True)  # Default to using cache
        # Add missing translation keys safely
        try:
            if "use_cache" not in current_language:
                # These translations will be added at runtime
                use_cache_en = "Use Cache (Faster)"
                use_cache_da = "Brug cache (Hurtigere)"
        except:
            pass
        cache_checkbox = tk.Checkbutton(checkbox_frame, text=current_language.get("use_cache", "Use Cache"), variable=use_cache_entry)
        cache_checkbox.pack(anchor="w", pady=2)
        
        # Quality options in a separate frame - New feature for NEF optimization
        quality_frame = tk.Frame(root)
        quality_frame.grid(row=8, column=0, columnspan=3, sticky="w", padx=10, pady=5)
        
        # Define quality options with fallbacks
        quality_label = tk.Label(quality_frame, text=current_language.get("image_quality", "Image Quality:"))
        quality_label.pack(side=tk.LEFT, padx=(0, 10))
        quality_label = tk.Label(quality_frame, text=current_language.get("image_quality", "Image Quality:"))
        quality_label.pack(side=tk.LEFT, padx=(0, 10))
        
        quality_var = tk.StringVar()
        quality_var.set("normal")  # Default to normal quality
        
        # Radio buttons for quality options
        low_radio = tk.Radiobutton(quality_frame, text="Low (Fast)", 
                                  variable=quality_var, value="low")
        low_radio.pack(side=tk.LEFT, padx=5)
        
        normal_radio = tk.Radiobutton(quality_frame, text="Normal", 
                                     variable=quality_var, value="normal")
        normal_radio.pack(side=tk.LEFT, padx=5)
        
        high_radio = tk.Radiobutton(quality_frame, text="High (Best)", 
                                   variable=quality_var, value="high")
        high_radio.pack(side=tk.LEFT, padx=5)

        # Start Button
        start_button = tk.Button(root, text=current_language["start_processing"], command=start_processing)
        start_button.grid(row=9, column=0, columnspan=3, pady=20)
        # Make the start button larger and more prominent
        start_button.config(height=2, width=20, bg="#d0f0d0", font=("Arial", 10, "bold"))

        root.mainloop()
except Exception as e:
    # Create a simple GUI to show the error
    import tkinter as tk
    from tkinter import messagebox
    import traceback
    
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error Starting Application", 
                         f"Error: {e}\n\n{traceback.format_exc()}")
    root.destroy()