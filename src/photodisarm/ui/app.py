import tkinter as tk
from tkinter import filedialog, messagebox
import os
import traceback

# Import the core viewer and other utilities
from ..core.viewer import ImageViewer
from ..utils.util import center_window
from ..i18n.localization import localization


class PhotoDisarmApp:
    """Main application class that handles the GUI interface."""
    
    def __init__(self):
        self.root = None
        self.image_viewer = ImageViewer()
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the main GUI interface."""
        # Setting up the GUI
        self.root = tk.Tk()
        self.root.title(localization.get_text("window_title"))
        center_window(self.root, width=500, height=450)  # Increase width to accommodate longer text

        # Configure the grid to center content horizontally
        self.root.columnconfigure(0, weight=3)  # More weight for the label column
        self.root.columnconfigure(1, weight=5)  # Input field column
        self.root.columnconfigure(2, weight=1)  # For buttons

        self._create_language_button()
        self._create_input_fields()
        self._create_parameter_fields()
        self._create_checkboxes()
        self._create_quality_options()
        self._create_start_button()

    def _create_language_button(self):
        """Create the language switch button."""
        # Language Button - Move to top left corner
        language_button = tk.Button(self.root, text=localization.get_text("switch_lang"), command=localization.switch_language)
        language_button.grid(row=0, column=0, sticky="nw", padx=10, pady=10)
        
        # Give the language button a distinctive color
        language_button.config(bg="#e0e0ff")

    def _create_input_fields(self):
        """Create input and output directory fields."""
        # Input Directory - Moved down one row
        self.input_path = tk.StringVar()
        input_dir_label = tk.Label(self.root, text=localization.get_text("input_dir"), anchor="e", width=20)
        input_dir_label.grid(row=1, column=0, sticky="e", padx=5, pady=5)
        
        input_entry = tk.Entry(self.root, textvariable=self.input_path, width=40)
        input_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.input_path.set(os.getcwd())
        
        # Browse button
        browse_button = tk.Button(
            self.root, 
            text=localization.get_text("browse"), 
            command=lambda: self.input_path.set(filedialog.askdirectory(initialdir=os.getcwd()))
        )
        browse_button.grid(row=1, column=2, sticky="w", padx=5)

        # Add Output Directory - Using the next row
        self.output_path = tk.StringVar()
        output_dir_label = tk.Label(self.root, text=localization.get_text("output_dir"), anchor="e", width=20)
        output_dir_label.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        
        output_entry = tk.Entry(self.root, textvariable=self.output_path, width=40)
        output_entry.grid(row=2, column=1, sticky="ew", padx=5)
        self.output_path.set(os.path.join(os.getcwd(), "output"))  # Default to 'output' subfolder
        
        # Output Browse button
        output_browse_button = tk.Button(
            self.root, 
            text=localization.get_text("browse"), 
            command=lambda: self.output_path.set(filedialog.askdirectory(initialdir=self.output_path.get()))
        )
        output_browse_button.grid(row=2, column=2, sticky="w", padx=5)

    def _create_parameter_fields(self):
        """Create parameter input fields."""
        # Threshold
        threshold_label = tk.Label(self.root, text=localization.get_text("threshold"), anchor="e", width=20)
        threshold_label.grid(row=3, column=0, sticky="e", padx=5, pady=5)
        
        self.threshold_entry = tk.Entry(self.root, width=10)
        self.threshold_entry.insert(0, "150.0")
        self.threshold_entry.grid(row=3, column=1, sticky="w", padx=5)

        # Chunk Size
        chunk_size_label = tk.Label(self.root, text=localization.get_text("chunk_size"), anchor="e", width=20)
        chunk_size_label.grid(row=4, column=0, sticky="e", padx=5, pady=5)
        
        self.chunk_size_entry = tk.Entry(self.root, width=10)
        self.chunk_size_entry.insert(0, "100")
        self.chunk_size_entry.grid(row=4, column=1, sticky="w", padx=5)

        # Max Width
        width_label = tk.Label(self.root, text=localization.get_text("max_width"), anchor="e", width=20)
        width_label.grid(row=5, column=0, sticky="e", padx=5, pady=5)
        
        self.width_entry = tk.Entry(self.root, width=10)
        self.width_entry.insert(0, "1720")
        self.width_entry.grid(row=5, column=1, sticky="w", padx=5)

        # Max Height
        height_label = tk.Label(self.root, text=localization.get_text("max_height"), anchor="e", width=20)
        height_label.grid(row=6, column=0, sticky="e", padx=5, pady=5)
        
        self.height_entry = tk.Entry(self.root, width=10)
        self.height_entry.insert(0, "1000")
        self.height_entry.grid(row=6, column=1, sticky="w", padx=5)

    def _create_checkboxes(self):
        """Create checkbox options."""
        # Checkboxes in a new frame for better organization
        checkbox_frame = tk.Frame(self.root)
        checkbox_frame.grid(row=7, column=0, columnspan=3, sticky="w", padx=10, pady=10)
        
        # Move Duplicates Checkbox
        self.move_duplicates_entry = tk.IntVar()
        self.move_duplicates_entry.set(False)
        duplicates_checkbox = tk.Checkbutton(checkbox_frame, text=localization.get_text("delete_duplicates"), variable=self.move_duplicates_entry)
        duplicates_checkbox.pack(anchor="w", pady=2)
        
        # Recursive Search Checkbox
        self.recursive_search_entry = tk.IntVar()
        self.recursive_search_entry.set(True)
        recursive_checkbox = tk.Checkbutton(checkbox_frame, text=localization.get_text("search_recursively"), variable=self.recursive_search_entry)
        recursive_checkbox.pack(anchor="w", pady=2)
        
        # Add "Use Cache" checkbox - New feature for NEF optimization
        self.use_cache_entry = tk.IntVar()
        self.use_cache_entry.set(True)  # Default to using cache
        # Add missing translation keys safely
        cache_checkbox = tk.Checkbutton(checkbox_frame, text=localization.get_text("use_cache"), variable=self.use_cache_entry)
        cache_checkbox.pack(anchor="w", pady=2)

    def _create_quality_options(self):
        """Create quality selection options."""
        # Quality options in a separate frame - New feature for NEF optimization
        quality_frame = tk.Frame(self.root)
        quality_frame.grid(row=8, column=0, columnspan=3, sticky="w", padx=10, pady=5)
        
        # Define quality options with fallbacks
        quality_label = tk.Label(quality_frame, text=localization.get_text("image_quality"))
        quality_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.quality_var = tk.StringVar()
        self.quality_var.set("normal")  # Default to normal quality
        
        # Radio buttons for quality options
        low_radio = tk.Radiobutton(quality_frame, text="Low (Fast)", 
                                  variable=self.quality_var, value="low")
        low_radio.pack(side=tk.LEFT, padx=5)
        
        normal_radio = tk.Radiobutton(quality_frame, text="Normal", 
                                     variable=self.quality_var, value="normal")
        normal_radio.pack(side=tk.LEFT, padx=5)
        
        high_radio = tk.Radiobutton(quality_frame, text="High (Best)", 
                                   variable=self.quality_var, value="high")
        high_radio.pack(side=tk.LEFT, padx=5)

    def _create_start_button(self):
        """Create the start processing button."""
        # Start Button
        start_button = tk.Button(self.root, text=localization.get_text("start_processing"), command=self.start_processing)
        start_button.grid(row=9, column=0, columnspan=3, pady=20)
        # Make the start button larger and more prominent
        start_button.config(height=2, width=20, bg="#d0f0d0", font=("Arial", 10, "bold"))

    def start_processing(self):
        """Start the image processing workflow."""
        try:
            input_dir = self.input_path.get()
            output_dir = self.output_path.get()
            max_width = int(self.width_entry.get())
            max_height = int(self.height_entry.get())
            move_duplicates = bool(self.move_duplicates_entry.get())
            recursive = bool(self.recursive_search_entry.get())
            chunk_size = int(self.chunk_size_entry.get())
            use_cache = bool(self.use_cache_entry.get())
            quality = self.quality_var.get()

            # Start processing using the image viewer
            self.image_viewer.start_processing(
                input_dir=input_dir,
                output_dir=output_dir,
                max_width=max_width,
                max_height=max_height,
                move_duplicates=move_duplicates,
                recursive=recursive,
                chunk_size=chunk_size,
                use_cache=use_cache,
                quality=quality
            )
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during processing: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for the application."""
    try:
        app = PhotoDisarmApp()
        app.run()
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


if __name__ == "__main__":
    main()
