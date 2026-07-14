import os
import numpy as np
import pandas as pd
from tifffile import imread, imwrite
import torch
import cv2
import sys

folder = sys.argv[1]

out_folder = sys.argv[2]

def preprocess_image(img, apply_blur=False):
    # Normalize to 8-bit for CLAHE
    img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Apply CLAHE (adaptive histogram equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_eq = clahe.apply(img_norm)

    # Optionally smooth image
    if apply_blur:
        img_eq = cv2.GaussianBlur(img_eq, (3, 3), 0)

    return img_eq

def apply_CLAHE(folder_path, out_folder, apply_blur=False):
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.tif', '.tiff'))]
    results = []

    for image_name in image_files:
        image_path = os.path.join(folder_path, image_name)
        img = imread(image_path)

        # Convert multi-dimensional image to 2D grayscale
        if img.ndim > 2:
            img = img[0] if img.shape[0] < img.shape[-1] else img[..., 0]

        # Preprocess
        img_preprocessed = preprocess_image(img, apply_blur=apply_blur)
        
        imwrite(os.path.join(out_folder, image_name), img_preprocessed)
        

apply_CLAHE(folder, out_folder, False)
