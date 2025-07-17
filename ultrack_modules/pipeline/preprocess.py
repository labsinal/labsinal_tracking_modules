"""
Module that applies labsinal's preprocess for tracking
"""
#########################################
# imports
from tifffile import imwrite
from multiprocessing import Pool
from ultrack.imgproc import register_timelapse
import cv2
import tifffile
import numpy as np
import os
from tqdm import tqdm
from scipy.ndimage import gaussian_filter
from scipy.signal import find_peaks
import dask.array as da

#########################################
# Define helper functions

def check_file_unfocused(file_path: str) -> bool:
    """
    Function to check if a file is unfocused based on image analysis.

    params:
        file_path (str): Path to the image file.
    returns:
        bool: True if the file is unfocused, False otherwise.
    """
    # Open image
    file = tifffile.imread(file_path)

    # Calculate the mean for each row
    means = np.array([np.mean(row) for row in file])

    # Calculate smoothed curve
    smooth = gaussian_filter(means, sigma=10)

    # Find peaks in the smoothed curve
    peaks, _ = find_peaks(smooth, prominence=0.5)

    # Return True if no peaks are found, indicating the file is unfocused
    return len(peaks) > 0

def filter_unfocused_files(input_dir: str) -> list[str]:
    """
    Function to filter out unfocused files based on image analysis.

    params:
        input_dir (str): Directory containing the image files to be filtered.
    returns:
        List: The function saves the filtered files in the specified output directory.
    """
    # Get all files in the input directory
    files = os.listdir(input_dir)
    filepaths = [os.path.join(input_dir, f) for f in files if f.endswith('.tif') or f.endswith('.tiff')]

    # Use multiprocessing to check files in parallel
    with Pool() as pool:
        results = pool.map(check_file_unfocused, filepaths)

    focused = [f for f, keep in zip(filepaths, results) if keep]
    unfocused = set(filepaths) - set(focused)

    return focused, unfocused

def apply_clahe(img):
    """
    Function that applies clahe filter to a image

    params:
    img_path | image path
    """
    
    CLAHE = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    # open image
    # Normalize to 8-bit for CLAHE
    img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Apply CLAHE (adaptive histogram equalization)
    img_eq = CLAHE.apply(img_norm)

    return img_eq

def preprocess_images(input_path: str):
    """
    Function that applies preprocess from labsinal's tracking pipeline

    params:
    input_path:str | path to folder containing unprocessed images
    """
    focused, _ = filter_unfocused_files(input_path)

    focused = [f for f in sorted(focused)]  # garante ordem alfabética consistente
    focused_images = da.stack([da.from_array(tifffile.imread(f), chunks="auto") for f in focused])

    registered_images = register_timelapse(focused_images)

    # apply CLAHE in order
    with Pool() as pool:
        clahed_images = list(tqdm(pool.imap(apply_clahe, registered_images), total=len(registered_images), desc="Applying CLAHE"))

    filenames = list(map(os.path.basename, focused))

    return clahed_images, filenames


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

    os.makedirs(args.output_path, exist_ok=True)

    for img, filename in zip(processed_images, filenames):
        print(filename)
        save_path = os.path.join(args.output_path, filename)
        imwrite(save_path, img)
    
    print("Done!")

#########################################
# Excecute if runned directly
if __name__ == "__main__": main()
