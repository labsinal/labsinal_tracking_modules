"""
Module that applies labsinal's preprocess for tracking
"""
#########################################
# imports
from tifffile import imread, imwrite
from multiprocessing import Pool
from ultrack.imgproc import register_timelapse
import cv2
import numpy as np
import os
from tqdm import tqdm

#########################################
# Define helper functions

def open_and_apply_clahe(img_path):
    """
    Function that opens and applies clahe filter to a image

    params:
    img_path | image path
    """
    
    CLAHE = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    # open image
    img = imread(img_path)

    # Normalize to 8-bit for CLAHE
    img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Apply CLAHE (adaptive histogram equalization)
    img_eq = CLAHE.apply(img_norm)

    return img_eq

def preprocess_images(input_path:str):
    """
    Function that applies preprocess from labsinal's tracking pipeline

    params:
    input_path:str | path fto folder containing unprocessed images
    """
    # get paths in order
    filenames = sorted([x for x in os.listdir(input_path) if x.endswith((".tif", ".tiff"))])
    filepaths = [os.path.join(input_path, x) for x in filenames]

    # apply clahe in parallel
    clahed_images = []
    with Pool() as pool:
        with tqdm(total=len(filepaths), desc="Applying CLAHE") as pbar:
            clahed_images = []
            for result in pool.imap_unordered(open_and_apply_clahe, filepaths):
                clahed_images.append(result)
                pbar.update(1)

    clahed_images = np.array(clahed_images)

    # register timelapse
    registered_images = register_timelapse(clahed_images)

    # return processed images
    return registered_images, filenames

#########################################
# Define code's main function
def main() -> None:
    """
    Code's main function
    """
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument("-i", "--input",
                        action="store",
                        dest="input_path",
                        help="Path to folder containing unprocessed images.")
    
    parser.add_argument("-o", "--output",
                        action="store",
                        dest="output_path",
                        help="Path to folder where processed images will be saved.")
    
    args= parser.parse_args()

    processed_images, filenames = preprocess_images(args.input_path)

    for img, filename in zip(processed_images, filenames):
        save_path = os.path.join(args.output_path, filename)
        imwrite(save_path, img)
    
    print("Done!")

#########################################
# Excecute if runned directly
if __name__ == "__main__": main()