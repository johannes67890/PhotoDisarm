from PIL import Image
import hashlib


def add(image_paths: list):
    dupSet = set()
    newList = []
    for image_path in image_paths:
        md5hash = hashlib.md5(Image.open(image_path).tobytes())

        if md5hash.hexdigest() in dupSet:
            continue
        else:
            dupSet.add(md5hash.hexdigest())
            newList.append(image_path)
            print(f"Added {image_path} to the set")
    return newList
            
        

