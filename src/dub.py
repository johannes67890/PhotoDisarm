from PIL import Image
import hashlib
import shutil  # For moving files
import os

def add(image_paths: list):
    dupSet = set()
    newList = []
    for image_path in image_paths:
        md5hash = hashlib.md5(Image.open(image_path).tobytes())

        if md5hash.hexdigest() in dupSet:
            if os.path.exists("duplicates"):
                shutil.move(image_path, "duplicates")
            else:
                os.makedirs("duplicates", exist_ok=True)
                shutil.move(image_path, "duplicates")
            continue
        else:
            dupSet.add(md5hash.hexdigest())
            newList.append(image_path)
    return newList
            
        

