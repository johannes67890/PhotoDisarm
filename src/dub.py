from PIL import Image
import hashlib
import shutil
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

def hash_image(image_path):
    with Image.open(image_path) as img:
        # Only hash part of the image if speed > exactness
        return hashlib.md5(img.tobytes()).hexdigest()

def add(image_paths: list):
    dupSet = set()
    newList = []
    
    # Ensure the duplicates directory exists once
    duplicates_dir = "duplicates"
    os.makedirs(duplicates_dir, exist_ok=True)
    
    print("Checking & moveing duplicates... \n")
    with ThreadPoolExecutor() as executor:
        for image_path, md5hash in tqdm(zip(image_paths, executor.map(hash_image, image_paths)), total=len(image_paths)):
            if md5hash in dupSet:
                shutil.move(image_path, duplicates_dir)
            else:
                dupSet.add(md5hash)
                newList.append(image_path)
    
    print(f"\n{len(image_paths) - len(newList)} duplicates found and moved to {duplicates_dir}")
    return newList

