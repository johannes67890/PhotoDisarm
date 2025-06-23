"""
Entry point for running the application with the -m flag
"""
from photodisarm.ui.app import PhotoDisarmApp

def main():
    """Run the PhotoDisarm application"""
    app = PhotoDisarmApp()
    app.run()

if __name__ == "__main__":
    main()
