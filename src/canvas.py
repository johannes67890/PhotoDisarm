import cv2
import rawpy
import numpy as np
import os
import argparse
from glob import glob
from multiprocessing import Pool, cpu_count
import shutil  # For moving files
import dub
import threading


def display_message(message, width, height):
    # Create a blank image
    blank_image = np.zeros((height, width, 3), dtype=np.uint8)
    # Set text parameters
    cv2.putText(blank_image, message, (50, height // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    return blank_image


def resize_image(image, max_width, max_height):
    (h, w) = image.shape[:2]
    aspect_ratio = w / h

    # Calculate new dimensions while maintaining aspect ratio
    if w > h:
        new_width = min(w, max_width)
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = min(h, max_height)
        new_width = int(new_height * aspect_ratio)

    # Ensure new dimensions don't exceed the maximum allowed dimensions
    if new_width > max_width or new_height > max_height:
        # Scale down to fit within max dimensions
        scale_factor = min(max_width / w, max_height / h)
        new_width = int(w * scale_factor)
        new_height = int(h * scale_factor)

    # Resize the image to the new dimensions
    resized_image = cv2.resize(image, (new_width, new_height))

    # Create a blank canvas with max dimensions
    canvas = np.zeros((max_height, max_width, 3), dtype=np.uint8)

    # Calculate center position
    y_offset = (max_height - new_height) // 2
    x_offset = (max_width - new_width) // 2

    # Place the resized image on the canvas, if it fits
    canvas[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_image

    return canvas