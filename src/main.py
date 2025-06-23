"""
Main entry point for PhotoDisarm application
"""
import sys
import os
import tkinter as tk
from tkinter import messagebox
import traceback

# Add the src directory to the Python path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from photodisarm.ui.app import PhotoDisarmApp

    if __name__ == "__main__":
        app = PhotoDisarmApp()
        app.run()
except Exception as e:
    # Create a simple GUI to show the error
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error Starting Application", 
                         f"Error: {e}\n\n{traceback.format_exc()}")
    root.destroy()
    sys.exit(1)
