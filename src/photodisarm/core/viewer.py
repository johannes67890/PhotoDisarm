import cv2
import numpy as np
import os
import shutil
from glob import glob
from multiprocessing import Pool, cpu_count
from collections import deque
import asyncio
import threading
import queue
import time
from tkinter import messagebox

# Import your other modules
from ..ui.canvas import display_message, put_text_utf8, resize_image
from ..utils.util import center_window, sort_images_by_date, get_image_metadata_date, move_image_to_dir_with_date, get_images_rec, get_images
from ..processing.duplicates import duplicates
from ..processing.corrupt import CorruptDetector
from ..processing.image import Image_processing
from ..i18n.localization import localization
from ..processing.background import BackgroundProcessor


class ImageViewer:
    """Core image viewer class that handles image processing and display logic."""
    
    def __init__(self):
        self.background_processor = None
        
    async def process_images(self, image_paths: list, max_width: int, max_height: int, chunk_size: int = 50, output_dir: str = None, use_cache: bool = True, quality: str = 'normal', save_keybind: str = 'space', delete_keybind: str = 'backspace', sort_by_date: bool = True):
        """
        Process images in chunks to reduce memory usage.
        
        Args:
            image_paths: List of paths to images
            max_width: Maximum width for image display
            max_height: Maximum height for image display
            chunk_size: Number of images to load into memory at once
            output_dir: Directory for organized output files
            use_cache: Whether to use caching for image processing            quality: Image quality setting ('low', 'normal', 'high')
            save_keybind: Key binding for saving images (default: 'space')
            delete_keybind: Key binding for deleting images (default: 'backspace')
            sort_by_date: Whether images are already sorted by date globally
        """
        index: int = 0
        total_images = len(image_paths)
        # Use deque with maxlen=10 to automatically limit history size
        history = deque(maxlen=10)
        
        # Key mapping function
        def get_key_code(key_name: str) -> int:
            """Map key names to OpenCV key codes"""
            key_map = {
                'space': 32,
                'spacebar': 32,
                'backspace': 8,
                'delete': 3014656,
                'enter': 13,
                'return': 13,
                'tab': 9,
                'escape': 27,
                'esc': 27,
                'up': 2490368,
                'down': 2621440,
                'left': 2424832,
                'right': 2555904,
                'home': 2359296,
                'end': 2293760,
                'pageup': 2162688,
                'pagedown': 2228224,
                'insert': 2097152,
                'f1': 7340032, 'f2': 7405568, 'f3': 7471104, 'f4': 7536640,
                'f5': 7602176, 'f6': 7667712, 'f7': 7733248, 'f8': 7798784,
                'f9': 7864320, 'f10': 7929856, 'f11': 7995392, 'f12': 8060928,
                'a': ord('a'), 'b': ord('b'), 'c': ord('c'), 'd': ord('d'), 'e': ord('e'),
                'f': ord('f'), 'g': ord('g'), 'h': ord('h'), 'i': ord('i'), 'j': ord('j'),
                'k': ord('k'), 'l': ord('l'), 'm': ord('m'), 'n': ord('n'), 'o': ord('o'),
                'p': ord('p'), 'q': ord('q'), 'r': ord('r'), 's': ord('s'), 't': ord('t'),
                'u': ord('u'), 'v': ord('v'), 'w': ord('w'), 'x': ord('x'), 'y': ord('y'),
                'z': ord('z'),
                '0': ord('0'), '1': ord('1'), '2': ord('2'), '3': ord('3'), '4': ord('4'),
                '5': ord('5'), '6': ord('6'), '7': ord('7'), '8': ord('8'), '9': ord('9')
            }
            return key_map.get(key_name.lower(), 32)  # Default to space if key not found
        
        # Get the key codes for save and delete actions
        save_key_code = get_key_code(save_keybind)
        delete_key_code = get_key_code(delete_keybind)
  
        # Helper function to determine image status based on path
        def get_image_status(img_path: str) -> str:
            """
            Get the status text for an image based on its path
            
            Args:
                img_path: Path to the image file
                
            Returns:
                Status text ('Saved', 'Deleted', or '')
            """
            if output_dir and output_dir in img_path and "Deleted" not in img_path:
                return localization.get_text("status_saved")
            elif "Deleted" in img_path:
                return localization.get_text("status_deleted")
            else:
                return localization.get_text("status_skipped")
            
        cv2.namedWindow(localization.get_text("image_window"), cv2.WINDOW_NORMAL)
        cv2.resizeWindow(localization.get_text("image_window"), max_width, max_height)
        
        # Process images in chunks
        self.background_processor = BackgroundProcessor(max_queue_size=50)
        
        while index < total_images:
            # Calculate the end index for current chunk
            chunk_end = min(index + chunk_size, total_images)
              # Extract current chunk of image paths
            chunk_paths = image_paths[index:chunk_end]
            
            # Sort this chunk by date only if global sorting wasn't done
            if not sort_by_date:
                chunk_paths = sort_images_by_date(chunk_paths)
                # Update the original list with the sorted chunk
                image_paths[index:chunk_end] = chunk_paths
            
            # Start background processor for this chunk and prepare for next chunk
            self.background_processor.start(
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
                
                # Update background processor's current index for accurate prefetching
                self.background_processor.current_index = current_chunk_index
                
                # Get image from background processor (it will process immediately if not preloaded)
                start_time = time.time()
                _, imageData = self.background_processor.get_image(imagePath)
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
                image_date = get_image_metadata_date(imagePath)
                date_info = f"{image_date}" if image_date else localization.get_text("no_date")
                
                # Display position info in bottom left corner using custom UTF-8 text function
                position_text = f"{localization.get_text('image_window')} {current_index + 1}/{total_images}"
                status_image = put_text_utf8(
                    status_image,
                    position_text,
                    position=(10, max_height - 30),
                    font_size=18, 
                    color=(255, 255, 255),
                    thickness=2,
                    with_background=True  # Add semi-transparent background
                )
                
                # Display keybindings in bottom middle
                keybinding_text = f"{save_keybind.title()}: Gem | {delete_keybind.title()}: Slet | ← : Tilbage | → : Frem"
                # Calculate the center position (roughly)
                text_width = len(keybinding_text) * 7  # Rough estimate for font size 18
                center_x = (max_width - text_width) // 2
                status_image = put_text_utf8(
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
                    if current_status == localization.get_text("status_saved"):
                        status_color = (0, 255, 0)  # Green for saved
                    elif current_status == localization.get_text("status_deleted"):
                        status_color = (0, 0, 255)  # Red (BGR format) for deleted
                    else:
                        status_color = (255, 255, 255)  # White for skipped
                            
                    status_image = put_text_utf8(
                        status_image,
                        current_status,
                        position=(max_width - 150, 30),
                        font_size=16,
                        color=status_color,
                        thickness=2,
                        with_background=True
                    )

                # Display date info in bottom right corner
                status_image = put_text_utf8(
                    status_image,
                    date_info,
                    position=(max_width - len(date_info) * 10 - 20, max_height - 30),
                    font_size=18,
                    color=(255, 255, 255),
                    thickness=2,
                    with_background=True  # Add semi-transparent background
                )
            
                cv2.imshow(localization.get_text("image_window"), status_image)
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
                elif key in (83, 2555904, 39, 65363): # Right arrow key codes
                    # For any other key, store in history as skipped and move to next image
                    history.append(imagePath)
                    current_chunk_index += 1
                # Store current image in history before processing action
                if key == save_key_code:  # Configurable save key
                    history.append(imagePath)
                    new_path = move_image_to_dir_with_date(imagePath, output_dir)
                    # Update the path in the original list
                    image_paths[current_index] = new_path
                    current_chunk_index += 1
                elif key == delete_key_code:  # Configurable delete key
                    history.append(imagePath)
                    deleted_dir = os.path.join(output_dir, "Deleted") if output_dir else "Deleted"
                    os.makedirs(deleted_dir, exist_ok=True)
                    image_name = os.path.basename(imagePath)
                    new_path = os.path.join(deleted_dir, image_name)
                    shutil.move(imagePath, new_path)
                    image_paths[current_index] = new_path
                    current_chunk_index += 1                
                elif key == 27 or key == -1:  # Esc key
                    if self.background_processor:
                        self.background_processor.stop()  # Stop background processing
                    cv2.destroyAllWindows()
                    return

            
            # Move to the next chunk
            index = chunk_end
          # All chunks processed
        if self.background_processor:
            self.background_processor.stop()  # Stop background processing
        messagebox.showinfo(localization.get_text("done"), localization.get_text("all_processed"))
        cv2.destroyAllWindows()

    def start_processing(self, input_dir: str, output_dir: str, max_width: int, max_height: int, 
                        move_duplicates: bool, recursive: bool, chunk_size: int, 
                        use_cache: bool = True, sort_by_date: bool = True, quality: str = 'normal',
                        save_keybind: str = 'space', delete_keybind: str = 'backspace', 
                        detect_corrupt: bool = False):
        """
        Start the image processing workflow.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            max_width: Maximum width for image display
            max_height: Maximum height for image display            move_duplicates: Whether to move duplicate images
            recursive: Whether to search recursively
            chunk_size: Number of images to process in each chunk
            use_cache: Whether to use caching
            sort_by_date: Whether to sort all images by date before processing            quality: Image quality setting
            save_keybind: Key binding for saving images (default: 'space')
            delete_keybind: Key binding for deleting images (default: 'backspace')
            detect_corrupt: Whether to detect and move corrupt images before processing
        """
        if not os.path.isdir(input_dir):
            messagebox.showerror(localization.get_text("error"), localization.get_text("invalid_dir"))
            return

        image_paths = []
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)        
        if recursive:
            for chunk in get_images_rec(input_dir):
                image_paths.extend(chunk)
        else:
            for chunk in get_images(input_dir):
                image_paths.extend(chunk)
        
        print(f"Found {len(image_paths)} images")
        
        # Detect and move corrupt images if requested
        if detect_corrupt:
            print("Detecting corrupt images...")
            image_paths = CorruptDetector.scan_for_corrupt_images(image_paths, output_dir)
            print(f"After corruption check: {len(image_paths)} valid images remaining")
        
        # Sort all images by date if requested
        if sort_by_date:
            print("Sorting all images by date...")
            image_paths = sort_images_by_date(image_paths)
            print("Images sorted by date")
        
        if move_duplicates:
            # Pass the output directory to add_with_progress
            image_paths = duplicates.add_with_progress(image_paths, output_dir)
            
        print(f"Processing {len(image_paths)} images in chunks of {chunk_size}")
        print(f"Image quality: {quality}, Cache enabled: {use_cache}")
          # Pass all parameters to process_images
        asyncio.run(self.process_images(image_paths, max_width, max_height, chunk_size, output_dir, use_cache, quality, save_keybind, delete_keybind, sort_by_date))
