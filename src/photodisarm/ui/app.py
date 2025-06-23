"""
Main application UI for PhotoDisarm

Provides the primary user interface for the application.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import asyncio
import threading
from typing import List, Dict, Tuple, Optional, Any

from photodisarm.i18n.localization import localization
from photodisarm.utils.file_utils import get_images, get_images_rec, center_window
from photodisarm.processing.duplicates import find_duplicates
from photodisarm.core.image_viewer import ImageViewer


class PhotoDisarmApp:
    """
    Main application class for PhotoDisarm
    
    Handles the application's user interface and coordinates
    between different components of the system.
    """
    
    def __init__(self):
        """Initialize the application"""
        self.root: Optional[tk.Tk] = None
        self.image_viewer = ImageViewer()
        
        # UI elements
        self.input_path = None
        self.output_path = None
        self.threshold_entry = None
        self.chunk_size_entry = None
        self.width_entry = None
        self.height_entry = None
        self.move_duplicates_entry = None
        self.recursive_search_entry = None
        self.use_cache_entry = None
        self.quality_var = None
        
        # Labels
        self.input_dir_label = None
        self.output_dir_label = None
        self.threshold_label = None
        self.chunk_size_label = None
        self.width_label = None
        self.height_label = None
        self.duplicates_checkbox = None
        self.recursive_checkbox = None
        self.language_button = None
        self.start_button = None
        self.browse_button = None
        self.output_browse_button = None
    
    def run(self):
        """Start the application"""
        # Create and configure the main window
        self.root = tk.Tk()
        self.root.title(localization.get_text("window_title"))
        center_window(self.root, width=500, height=450)
        
        # Configure grid
        self.root.columnconfigure(0, weight=3)  # Label column
        self.root.columnconfigure(1, weight=5)  # Input field column
        self.root.columnconfigure(2, weight=1)  # Button column
        
        # Build the UI
        self._create_ui()
        
        # Start the main loop
        self.root.mainloop()
    
    def _create_ui(self):
        """Create the application UI"""
        # Language Button - Move to top left corner
        self.language_button = tk.Button(
            self.root, 
            text=localization.get_text("switch_lang"), 
            command=self._switch_language
        )
        self.language_button.grid(row=0, column=0, sticky="nw", padx=10, pady=10)
        self.language_button.config(bg="#e0e0ff")
        
        # Input Directory
        self.input_path = tk.StringVar()
        self.input_dir_label = tk.Label(
            self.root, 
            text=localization.get_text("input_dir"), 
            anchor="e", 
            width=20
        )
        self.input_dir_label.grid(row=1, column=0, sticky="e", padx=5, pady=5)
        
        input_entry = tk.Entry(self.root, textvariable=self.input_path, width=40)
        input_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.input_path.set(os.getcwd())
        
        # Browse button
        self.browse_button = tk.Button(
            self.root, 
            text=localization.get_text("browse"), 
            command=lambda: self.input_path.set(filedialog.askdirectory(initialdir=os.getcwd()))
        )
        self.browse_button.grid(row=1, column=2, sticky="w", padx=5)
        
        # Output Directory
        self.output_path = tk.StringVar()
        self.output_dir_label = tk.Label(
            self.root, 
            text=localization.get_text("output_dir"), 
            anchor="e", 
            width=20
        )
        self.output_dir_label.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        
        output_entry = tk.Entry(self.root, textvariable=self.output_path, width=40)
        output_entry.grid(row=2, column=1, sticky="ew", padx=5)
        self.output_path.set(os.path.join(os.getcwd(), "output"))
        
        # Output Browse button
        self.output_browse_button = tk.Button(
            self.root, 
            text=localization.get_text("browse"), 
            command=lambda: self.output_path.set(filedialog.askdirectory(initialdir=self.output_path.get()))
        )
        self.output_browse_button.grid(row=2, column=2, sticky="w", padx=5)
        
        # Threshold
        self.threshold_label = tk.Label(
            self.root, 
            text=localization.get_text("threshold"), 
            anchor="e", 
            width=20
        )
        self.threshold_label.grid(row=3, column=0, sticky="e", padx=5, pady=5)
        
        self.threshold_entry = tk.Entry(self.root, width=10)
        self.threshold_entry.insert(0, "150.0")
        self.threshold_entry.grid(row=3, column=1, sticky="w", padx=5)
        
        # Chunk Size
        self.chunk_size_label = tk.Label(
            self.root, 
            text=localization.get_text("chunk_size"), 
            anchor="e", 
            width=20
        )
        self.chunk_size_label.grid(row=4, column=0, sticky="e", padx=5, pady=5)
        
        self.chunk_size_entry = tk.Entry(self.root, width=10)
        self.chunk_size_entry.insert(0, "100")
        self.chunk_size_entry.grid(row=4, column=1, sticky="w", padx=5)
        
        # Max Width
        self.width_label = tk.Label(
            self.root, 
            text=localization.get_text("max_width"), 
            anchor="e", 
            width=20
        )
        self.width_label.grid(row=5, column=0, sticky="e", padx=5, pady=5)
        
        self.width_entry = tk.Entry(self.root, width=10)
        self.width_entry.insert(0, "1720")
        self.width_entry.grid(row=5, column=1, sticky="w", padx=5)
        
        # Max Height
        self.height_label = tk.Label(
            self.root, 
            text=localization.get_text("max_height"), 
            anchor="e", 
            width=20
        )
        self.height_label.grid(row=6, column=0, sticky="e", padx=5, pady=5)
        
        self.height_entry = tk.Entry(self.root, width=10)
        self.height_entry.insert(0, "1000")
        self.height_entry.grid(row=6, column=1, sticky="w", padx=5)
        
        # Checkboxes in a new frame
        checkbox_frame = tk.Frame(self.root)
        checkbox_frame.grid(row=7, column=0, columnspan=3, sticky="w", padx=10, pady=10)
        
        # Move Duplicates Checkbox
        self.move_duplicates_entry = tk.IntVar()
        self.move_duplicates_entry.set(False)
        self.duplicates_checkbox = tk.Checkbutton(
            checkbox_frame, 
            text=localization.get_text("delete_duplicates"), 
            variable=self.move_duplicates_entry
        )
        self.duplicates_checkbox.pack(anchor="w", pady=2)
        
        # Recursive Search Checkbox
        self.recursive_search_entry = tk.IntVar()
        self.recursive_search_entry.set(True)
        self.recursive_checkbox = tk.Checkbutton(
            checkbox_frame, 
            text=localization.get_text("search_recursively"), 
            variable=self.recursive_search_entry
        )
        self.recursive_checkbox.pack(anchor="w", pady=2)
        
        # Use Cache Checkbox
        self.use_cache_entry = tk.IntVar()
        self.use_cache_entry.set(True)
        cache_checkbox = tk.Checkbutton(
            checkbox_frame, 
            text=localization.get_text("use_cache"), 
            variable=self.use_cache_entry
        )
        cache_checkbox.pack(anchor="w", pady=2)
        
        # Quality options in a separate frame
        quality_frame = tk.Frame(self.root)
        quality_frame.grid(row=8, column=0, columnspan=3, sticky="w", padx=10, pady=5)
        
        # Quality label
        quality_label = tk.Label(quality_frame, text=localization.get_text("image_quality"))
        quality_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Quality radio buttons
        self.quality_var = tk.StringVar()
        self.quality_var.set("normal")  # Default to normal quality
        
        low_radio = tk.Radiobutton(
            quality_frame, 
            text=localization.get_text("quality_low"), 
            variable=self.quality_var, 
            value="low"
        )
        low_radio.pack(side=tk.LEFT, padx=5)
        
        normal_radio = tk.Radiobutton(
            quality_frame, 
            text=localization.get_text("quality_normal"), 
            variable=self.quality_var, 
            value="normal"
        )
        normal_radio.pack(side=tk.LEFT, padx=5)
        
        high_radio = tk.Radiobutton(
            quality_frame, 
            text=localization.get_text("quality_high"), 
            variable=self.quality_var, 
            value="high"
        )
        high_radio.pack(side=tk.LEFT, padx=5)
        
        # Start Button
        self.start_button = tk.Button(
            self.root, 
            text=localization.get_text("start_processing"), 
            command=self._start_processing
        )
        self.start_button.grid(row=9, column=0, columnspan=3, pady=20)
        self.start_button.config(height=2, width=20, bg="#d0f0d0", font=("Arial", 10, "bold"))
    
    def _switch_language(self):
        """Switch the application language"""
        # Toggle between English and Danish
        localization.switch_language()
        
        # Update all UI text
        self.root.title(localization.get_text("window_title"))
        
        # Update all labels
        self.input_dir_label.config(text=localization.get_text("input_dir"))
        self.output_dir_label.config(text=localization.get_text("output_dir"))
        self.browse_button.config(text=localization.get_text("browse"))
        self.output_browse_button.config(text=localization.get_text("browse"))
        self.threshold_label.config(text=localization.get_text("threshold"))
        self.chunk_size_label.config(text=localization.get_text("chunk_size"))
        self.width_label.config(text=localization.get_text("max_width"))
        self.height_label.config(text=localization.get_text("max_height"))
        self.duplicates_checkbox.config(text=localization.get_text("delete_duplicates"))
        self.recursive_checkbox.config(text=localization.get_text("search_recursively"))
        self.start_button.config(text=localization.get_text("start_processing"))
        self.language_button.config(text=localization.get_text("switch_lang"))
    
    def _start_processing(self):
        """Start processing the images"""
        # Get values from UI
        input_dir = self.input_path.get()
        output_dir = self.output_path.get()
        max_width = int(self.width_entry.get())
        max_height = int(self.height_entry.get())
        move_duplicates = bool(self.move_duplicates_entry.get())
        recursive = bool(self.recursive_search_entry.get())
        chunk_size = int(self.chunk_size_entry.get())
        use_cache = bool(self.use_cache_entry.get())
        quality = self.quality_var.get()
        
        # Validate input directory
        if not os.path.isdir(input_dir):
            messagebox.showerror(
                localization.get_text("error"), 
                localization.get_text("invalid_dir")
            )
            return
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Collect image paths
        image_paths = []
        if recursive:
            for chunk in get_images_rec(input_dir):
                image_paths.extend(chunk)
        else:
            for chunk in get_images(input_dir):
                image_paths.extend(chunk)
        
        print(f"Found {len(image_paths)} images")
        
        # Handle duplicates if requested
        if move_duplicates:
            image_paths = find_duplicates(image_paths, output_dir)
        
        print(f"Processing {len(image_paths)} images in chunks of {chunk_size}")
        print(f"Image quality: {quality}, Cache enabled: {use_cache}")
        
        # Configure image viewer
        self.image_viewer.configure(
            max_width=max_width,
            max_height=max_height,
            output_dir=output_dir,
            use_cache=use_cache,
            quality=quality,
            chunk_size=chunk_size
        )
        
        # Start processing in a separate thread to keep UI responsive
        threading.Thread(
            target=self._run_processing,
            args=(image_paths,),
            daemon=True
        ).start()
    
    def _run_processing(self, image_paths: List[str]):
        """
        Run the image processing in a separate thread
        
        Args:
            image_paths: List of image paths to process
        """
        # Create and run a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Process images
            loop.run_until_complete(self.image_viewer.process_images(image_paths))
            
            # Show completion message
            if self.root and self.root.winfo_exists():
                messagebox.showinfo(
                    localization.get_text("done"),
                    localization.get_text("all_processed")
                )
        except Exception as e:
            print(f"Error processing images: {e}")
            if self.root and self.root.winfo_exists():
                messagebox.showerror(
                    localization.get_text("error"),
                    f"Error: {e}"
                )
        finally:
            loop.close()
