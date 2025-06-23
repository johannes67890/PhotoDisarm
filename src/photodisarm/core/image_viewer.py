"""
Image viewer component for PhotoDisarm

Provides the core image viewing functionality.
"""
import cv2
import os
import shutil
import asyncio
import time
from collections import deque
from typing import List, Dict, Tuple, Optional, Any, Callable
import numpy as np

from photodisarm.utils.file_utils import sort_images_by_date, get_image_metadata_date, move_image_to_dir_with_date
from photodisarm.i18n.localization import localization
from photodisarm.utils.drawing import put_text_utf8
from photodisarm.processing.background_processor import background_processor


class ImageViewer:
    """
    Image viewer component for displaying and managing images
    
    This class handles the image viewing and processing logic,
    including navigation, saving/deletion, and history management.
    """
    
    def __init__(self):
        """Initialize the image viewer"""
        self.history = deque(maxlen=10)  # Limited history size
        self.current_image_index = 0
        self.image_paths: List[str] = []
        self.max_width = 1000
        self.max_height = 800
        self.output_dir: Optional[str] = None
        self.use_cache = True
        self.quality = 'normal'
        self.chunk_size = 50
    
    def configure(self, max_width: int, max_height: int, 
                 output_dir: str, use_cache: bool = True,
                 quality: str = 'normal', chunk_size: int = 50) -> None:
        """
        Configure the image viewer
        
        Args:
            max_width: Maximum display width
            max_height: Maximum display height
            output_dir: Directory for saving images
            use_cache: Whether to use caching
            quality: Image quality setting ('low', 'normal', 'high')
            chunk_size: Size of each processing chunk
        """
        self.max_width = max_width
        self.max_height = max_height
        self.output_dir = output_dir
        self.use_cache = use_cache
        self.quality = quality
        self.chunk_size = chunk_size
    
    def get_image_status(self, img_path: str) -> str:
        """
        Get the status text for an image based on its path
        
        Args:
            img_path: Path to the image file
            
        Returns:
            Status text ('Saved', 'Deleted', or '')
        """
        if self.output_dir and self.output_dir in img_path and "Deleted" not in img_path:
            return localization.get_text("status_saved")
        elif "Deleted" in img_path:
            return localization.get_text("status_deleted")
        else:
            return localization.get_text("status_skipped")
    
    async def process_images(self, image_paths: List[str]) -> None:
        """
        Process and display images
        
        Args:
            image_paths: List of paths to images
        """
        self.image_paths = image_paths
        self.current_image_index = 0
        total_images = len(image_paths)
        # Clear history
        self.history.clear()
        
        # Create window for displaying images
        cv2.namedWindow(localization.get_text("image_window"), cv2.WINDOW_NORMAL)
        cv2.resizeWindow(localization.get_text("image_window"), self.max_width, self.max_height)
        
        # Process images in chunks
        while self.current_image_index < total_images:
            # Calculate the end index for current chunk
            chunk_start = (self.current_image_index // self.chunk_size) * self.chunk_size
            chunk_end = min(chunk_start + self.chunk_size, total_images)
            
            # Extract current chunk of image paths
            chunk_paths = image_paths[chunk_start:chunk_end]
            
            # Sort this chunk by date
            chunk_paths = sort_images_by_date(chunk_paths)
            
            # Update the original list with the sorted chunk
            image_paths[chunk_start:chunk_end] = chunk_paths
            
            # Log chunk info
            print(f"{localization.get_text('loading_chunk')} "
                  f"{chunk_start//self.chunk_size + 1}/{(total_images + self.chunk_size - 1)//self.chunk_size} "
                  f"({len(chunk_paths)} {localization.get_text('images')})")
            print(f"{localization.get_text('sorted_by_date')}: "
                  f"{', '.join([os.path.basename(p) for p in chunk_paths])}")
            
            # Start background processor for this chunk and prepare for next chunk
            background_processor.start(
                chunk_paths,                  # Current chunk paths
                self.current_image_index - chunk_start,  # Index within chunk
                self.max_width,
                self.max_height,
                self.use_cache,
                self.quality,
                self.chunk_size,              # Pass chunk size
                image_paths,                 # Pass all image paths for next chunk calculation
                chunk_start // self.chunk_size  # Current chunk index
            )
            
            # Process the current chunk
            continue_processing = await self._process_chunk(chunk_start, chunk_end)
            if not continue_processing:
                break
        
        # All chunks processed
        background_processor.stop()  # Stop background processing
        cv2.destroyAllWindows()
        
        return
    
    async def _process_chunk(self, chunk_start: int, chunk_end: int) -> bool:
        """
        Process a chunk of images
        
        Args:
            chunk_start: Starting index of the chunk
            chunk_end: Ending index of the chunk
            
        Returns:
            Whether to continue processing more chunks
        """
        # Process each image in the chunk
        while self.current_image_index < chunk_end and self.current_image_index < len(self.image_paths):
            imagePath = self.image_paths[self.current_image_index]
            print(f"{localization.get_text('processing_image')} "
                  f"{self.current_image_index + 1}/{len(self.image_paths)}: {imagePath}")
            
            # Update background processor's current index for accurate prefetching
            background_processor.current_index = self.current_image_index - chunk_start
            
            # Get image from background processor (it will process immediately if not preloaded)
            start_time = time.time()
            _, imageData = background_processor.get_image(imagePath)
            load_time = time.time() - start_time
            
            if load_time < 0.1:
                print(f"{localization.get_text('loaded_from_cache')} ({load_time:.3f}s)")
            else:
                print(f"Image processed in {load_time:.3f}s")
            
            if imageData is None:
                # Skip problematic images
                self.current_image_index += 1
                continue
            
            # Display the image with status information
            status_image = self._prepare_status_image(imageData, imagePath)
            cv2.imshow(localization.get_text("image_window"), status_image)
            
            # Handle keyboard input
            key = cv2.waitKeyEx(0)
            print(key)
            
            # Handle navigation and actions
            if key in (81, 2424832, 37, 65361):  # Left arrow key codes
                if self._handle_back_action():
                    # If we've gone back to a previous chunk, signal to restart from that point
                    return True
            elif key == 32:  # Space key (save)
                self._handle_save_action(imagePath)
            elif key == 8:  # Backspace key (delete)
                self._handle_delete_action(imagePath)
            elif key == 27 or key == -1:  # Esc key
                background_processor.stop()  # Stop background processing
                cv2.destroyAllWindows()
                return False
            else:
                # For any other key, store in history as skipped and move to next image
                self.history.append(imagePath)
                self.current_image_index += 1
        
        return True
    
    def _prepare_status_image(self, imageData: np.ndarray, imagePath: str) -> np.ndarray:
        """
        Prepare an image with status information overlaid
        
        Args:
            imageData: The image data
            imagePath: Path to the image file
            
        Returns:
            Image with status information
        """
        status_image = imageData.copy()
        
        # Try to get the image date
        image_date = get_image_metadata_date(imagePath)
        date_info = f"{image_date}" if image_date else localization.get_text("no_date")
          # Display position info in bottom left corner with better padding
        position_text = f"{localization.get_text('image_window')} {self.current_image_index + 1}/{len(self.image_paths)}"
        status_image = put_text_utf8(
            status_image,
            position_text,
            position=(20, self.max_height - 40),  # Increased padding from bottom/left
            font_size=18, 
            color=(255, 255, 255),
            thickness=2,
            with_background=True
        )
        
        # Display keybindings in bottom middle with better positioning
        keybinding_text = localization.get_text("keybindings")
        # Calculate the center position more accurately
        text_width = len(keybinding_text) * 8  # Better estimate for font size 18
        center_x = (self.max_width - text_width) // 2
        status_image = put_text_utf8(
            status_image,
            keybinding_text,
            position=(center_x, self.max_height - 40),  # Increased padding from bottom
            font_size=18,
            color=(255, 255, 255),
            thickness=2,
            with_background=True
        )
          # Add status in top right
        current_status = self.get_image_status(imagePath)
        if current_status:
            # Use different colors based on status
            if current_status == localization.get_text("status_saved"):
                status_color = (0, 255, 0)  # Green for saved
            elif current_status == localization.get_text("status_deleted"):
                status_color = (0, 0, 255)  # Red (BGR format) for deleted
            else:
                status_color = (255, 255, 255)  # White for skipped
            
            # Calculate better position based on text length
            status_width = len(current_status) * 10  # Estimate text width
            status_image = put_text_utf8(
                status_image,
                current_status,
                position=(self.max_width - status_width - 30, 40),  # Better top-right positioning
                font_size=18,  # Slightly larger text
                color=status_color,
                thickness=2,
                with_background=True
            )# Display date info in bottom right corner with improved positioning
        status_image = put_text_utf8(
            status_image,
            date_info,
            position=(self.max_width - len(date_info) * 10 - 30, self.max_height - 40),
            font_size=18,
            color=(255, 255, 255),
            thickness=2,
            with_background=True
        )
        
        return status_image
    
    def _handle_back_action(self) -> bool:
        """
        Handle going back to previous image
        
        Returns:
            Whether chunk processing needs to restart
        """
        if len(self.history) > 0:  # Only go back if history isn't empty
            prev_original_path = self.history.pop()
            
            # Update the current position to show the previous image
            try:
                prev_index = self.image_paths.index(prev_original_path)
                if prev_index < (self.current_image_index // self.chunk_size) * self.chunk_size:
                    # Need to go back to previous chunk
                    self.current_image_index = prev_index
                    return True  # Signal to restart chunk processing
                else:
                    # Same chunk
                    self.current_image_index = prev_index
            except ValueError:
                # Image not found in list, just go back one
                if self.current_image_index > 0:
                    self.current_image_index -= 1
        else:
            print("History limit reached, cannot go back further")
        
        return False
    
    def _handle_save_action(self, imagePath: str) -> None:
        """
        Handle saving an image
        
        Args:
            imagePath: Path to the image file
        """
        self.history.append(imagePath)
        if self.output_dir:
            new_path = move_image_to_dir_with_date(imagePath, self.output_dir)
            # Update the path in the original list
            self.image_paths[self.current_image_index] = new_path
        self.current_image_index += 1
    
    def _handle_delete_action(self, imagePath: str) -> None:
        """
        Handle deleting an image
        
        Args:
            imagePath: Path to the image file
        """
        self.history.append(imagePath)
        if self.output_dir:
            deleted_dir = os.path.join(self.output_dir, "Deleted")
        else:
            deleted_dir = "Deleted"
        
        os.makedirs(deleted_dir, exist_ok=True)
        image_name = os.path.basename(imagePath)
        new_path = os.path.join(deleted_dir, image_name)
        
        # Handle duplicate filenames
        counter = 1
        base_name, ext = os.path.splitext(image_name)
        while os.path.exists(new_path):
            new_path = os.path.join(deleted_dir, f"{base_name}_{counter}{ext}")
            counter += 1
        
        shutil.move(imagePath, new_path)
        self.image_paths[self.current_image_index] = new_path
        self.current_image_index += 1
