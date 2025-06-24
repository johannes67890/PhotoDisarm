try:
    # Import the main application
    from photodisarm.ui.app import main

    if __name__ == "__main__":
        main()
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
