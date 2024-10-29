import cv2
import rawpy
import numpy as np
import os
import argparse
from glob import glob
from multiprocessing import Pool, cpu_count
import canvas
import util
def variance_of_laplacian(image):
    return cv2.Laplacian(image, cv2.CV_64F).var()


def process_image(path:str, threshold, max_width, max_height):
    try:
        # Process NEF files with rawpy, others with OpenCV
        if path.lower().endswith('.nef'):
            with rawpy.imread(path) as raw:
                rgb_image = raw.postprocess()
            image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
        else:
            image = cv2.imread(path)
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Calculate blur measure
        fm = variance_of_laplacian(gray)
        text = "Not Blurry" 
        color = (0, 255, 0)
        if fm <= threshold: 
            text = "Blurry"
            color = (255, 0, 0)
        # Resize for display
        resized_image = canvas.resize_image(image, max_width, max_height)
        # Add text to the top of the image
        # util.printDateOnWindow(path)
        cv2.putText(resized_image, f"{text}: {fm:.2f}", (10, 30),
                    cv2.FONT_ITALIC, 0.8, color, 2)
        return path, resized_image
    except Exception as e:
        print(f"Error processing {path}: {e}")
        return None, None, None




