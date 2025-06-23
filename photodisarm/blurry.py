import cv2
import rawpy
import numpy as np
import os
from glob import glob
from multiprocessing import Pool, cpu_count
import photodisarm.canvas as canvas
import photodisarm.util as util
def variance_of_laplacian(image):
    return cv2.Laplacian(image, cv2.CV_64F).var()


def process_image(path:str, max_width, max_height):
    try:
        # Process NEF files with rawpy, others with OpenCV
        if path.lower().endswith('.nef'):
            with rawpy.imread(path) as raw:
                rgb_image = raw.postprocess()
            image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
        else:
            image = cv2.imread(path)
        # Resize for display
        resized_image = canvas.resize_image(image, max_width, max_height)
        # Add text to the top of the image
        # util.printDateOnWindow(path)
        return path, resized_image
    except Exception as e:
        print(f"Error processing {path}: {e}")
        return None, None, None




