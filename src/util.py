import os
from PIL import Image, ExifTags

def get_image_metadata_date(image_path):
    # Open the image file
    with open(image_path, "rb") as file:
        image = Image.open(file)
        # Get the image's Exif data
        exif_data = image.getexif()
        if exif_data is not None:
            # Get only DateTimeOriginal tag from the Exif data
            for tag_id, value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal":
                    return value
    return None
                

# Returns a list of image paths sorted by their creation date
def sort_images_by_date(image_paths: list):
    return sorted(image_paths, key=lambda x: os.path.getctime(x))