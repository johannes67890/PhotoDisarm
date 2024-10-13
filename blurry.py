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

def variance_of_laplacian(image):
    return cv2.Laplacian(image, cv2.CV_64F).var()

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

def process_image(imagePath, output_format, threshold, max_width, max_height):
    try:
        # Process NEF files with rawpy, others with OpenCV
        if imagePath.lower().endswith('.nef'):
            with rawpy.imread(imagePath) as raw:
                rgb_image = raw.postprocess()
            image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
        else:
            image = cv2.imread(imagePath)
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
        resized_image = resize_image(image, max_width, max_height)
        # Add text to the top of the image
        cv2.putText(resized_image, f"{text}: {fm:.2f}", (10, 30),
                    cv2.FONT_ITALIC, 0.8, color, 2)
        return resized_image, fm, text
    except Exception as e:
        print(f"Error processing {imagePath}: {e}")
        return None, None, None

def list_images(directory, valid_exts=(".jpg", ".jpeg", ".png", ".bmp", ".nef")):
    image_paths = []
    for ext in valid_exts:
        image_paths.extend(glob(os.path.join(directory, f"*{ext}")))
    return image_paths

def load_next_chunk(image_paths, chunk_size, current_index, result_list, output_format, threshold, max_width, max_height):
    # Load the next chunk of images in a separate thread
    next_chunk = image_paths[current_index:current_index + chunk_size]
    with Pool(processes=cpu_count()) as pool:
        results = pool.starmap(process_image, [(imagePath, output_format, threshold, max_width, max_height) for imagePath in next_chunk])
    result_list.clear()
    result_list.extend(results)

def display_message(message, width, height):
    # Create a blank image
    blank_image = np.zeros((height, width, 3), dtype=np.uint8)
    # Set text parameters
    cv2.putText(blank_image, message, (50, height // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    return blank_image

if __name__ == '__main__':
    # Parse arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--images", required=True, help="path to input directory of images")
    ap.add_argument("-t", "--threshold", type=float, default=150.0, help="focus measures that fall below this value will be considered 'blurry'")
    ap.add_argument("--format", type=str, default="png", choices=["png", "jpg"], help="desired output image format")
    ap.add_argument("--max-width", type=int, default=1720, help="maximum width of the displayed image")
    ap.add_argument("--max-height", type=int, default=1200, help="maximum height of the displayed image")
    ap.add_argument("--chunk-size", type=int, default=25, help="number of images to process at a time")
    args = vars(ap.parse_args())

    # Create directories to save images if they don't exist
    saved_dir = "saved_images"
    os.makedirs(saved_dir, exist_ok=True)

    delete_dir = "deleted_images"
    os.makedirs(delete_dir, exist_ok=True)

    # List images
    image_paths = dub.sort_images_by_date(list_images(args["images"]))
    result_list = []  # To store processed images

    current_index = 0  # To keep track of the current index in image_paths

    # Load the first chunk of images
    load_next_chunk(image_paths, args["chunk_size"], current_index, result_list, args["format"], args["threshold"], args["max_width"], args["max_height"])

    # Create a window with a fixed size
    cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Image", args["max_width"], args["max_height"])

    # Process and display images
    while current_index < len(image_paths):
        # Display each image in the result_list one by one
        for idx, (resized_image, fm, text) in enumerate(result_list):
            if resized_image is None:
                continue  # Skip if image processing failed

            # Get the corresponding image path for saving/deleting
            image_path = image_paths[current_index + idx]

            date = dub.get_image_metadata_date(image_path)
            (text_width, text_height), baseline = cv2.getTextSize(date, cv2.FONT_ITALIC, 0.8, 2)
            text_x = 10  # Padding from left
            text_y = resized_image.shape[0] - 10  # Padding from bottom
            cv2.rectangle(resized_image, (text_x - 5, text_y - text_height - baseline), (text_x + text_width + 5, text_y + 5), (255, 255, 255), -1)
            cv2.putText(resized_image, f"{date}", (text_x, text_y), cv2.FONT_ITALIC, 0.8, (0, 0, 0), 2)

            # Show the image with blur information
            cv2.imshow("Image", resized_image)
            print(f"Focus Measure: {fm:.2f} - {text}")

            # Wait for user to press a key to go to the next image
            key = cv2.waitKeyEx(0)


            # If 'space' (key 32) was pressed, save the image
            if key == 32:
                print("Saving image")
                # Move the image to the 'saved_images' directory
                image_name = os.path.basename(image_path)
                new_path = os.path.join(saved_dir, image_name)
                shutil.move(image_path, new_path)
                print(f"Image moved to: {new_path}")

            # If 'backspace' (key 8) was pressed, delete the image
            if key == 8:
                print("Deleting image")
                # Move the image to the 'deleted_images' directory
                image_name = os.path.basename(image_path)
                new_path = os.path.join(delete_dir, image_name)
                shutil.move(image_path, new_path)
                print(f"Image moved to: {new_path}")

            # If 'Esc' (key 27) was pressed, exit early
            if key == 27:
                break

            # Start loading the next chunk if we are on the third last image or lower
            if idx >= len(result_list) - 1 and current_index + args["chunk_size"] < len(image_paths):
                current_index += args["chunk_size"]  # Move to the next chunk index
                load_next_chunk(image_paths, args["chunk_size"], current_index, result_list, args["format"], args["threshold"], args["max_width"], args["max_height"])
                break  # Break out of the inner loop to load the next chunk

        # Break if 'Esc' was pressed
        if key == 27:
            break

    # Close all OpenCV windows
    cv2.destroyAllWindows()