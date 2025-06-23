"""
Simple launcher for PhotoDisarm

This file is the entry point for the application when run from the root directory.
"""
import os
import sys

# Add the src directory to the Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

if __name__ == "__main__":
    from photodisarm.ui.app import PhotoDisarmApp
    
    app = PhotoDisarmApp()
    app.run()
