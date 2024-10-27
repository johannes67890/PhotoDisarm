import os
from PIL import Image, ExifTags
from datetime import datetime
import shutil
from glob import glob
import dub as dup
import util as util

def get_images(directory, move_duplicates, valid_exts=(".jpg", ".jpeg", ".png", ".bmp", ".nef")) -> list:
    image_paths = []
    for ext in valid_exts:
        image_paths.extend(glob(os.path.join(directory, f"*{ext}"), recursive=True))

    if move_duplicates:
        image_paths = dup.add(image_paths)

    return util.sort_images_by_date(image_paths)

def get_image_metadata_date(image_path) -> str:
    # Open the image file
    with open(image_path, "rb") as file:
        image = Image.open(file)
        # Get the image's Exif data
        exif_data = image.getexif()
        if exif_data is not None:
            # Get only DateTimeOriginal tag from the Exif data
            for tag_id, value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal" or tag == "DateTime":
                    return value
    return None
                

# Returns a list of image paths sorted by their creation date
def sort_images_by_date(image_paths: list):
    return sorted(image_paths, key=lambda x: os.path.getctime(x))


def move_image_to_dir_with_date(image_path):
    date = datetime.strptime(get_image_metadata_date(image_path), "%Y:%m:%d %H:%M:%S")
    
    new_path = os.path.join(date.strftime("%Y"), date.strftime("%b"))

    print(f"Moving image to {os.path.dirname(new_path)}")
    if not os.path.exists(new_path):
        os.makedirs(new_path, exist_ok=True)
    shutil.move(image_path, new_path)


