"""
Module that segments cells using Cellpose (cyto3 model)
"""
#########################################
# Imports
import os
import numpy as np
from tifffile import imread, imwrite
from cellpose import models, io
import torch
from tqdm import tqdm
from argparse import ArgumentParser

#########################################
# Define helper functions

def segment_with_cellpose(image_path:str, model) -> tuple:
    """
    Segment an image using the Cellpose model (cyto3)

    params:
    image_path:str | path to input image
    model: Cellpose model instance

    returns:
    original image, mask, flow
    """
    img = imread(image_path)

    # Convert multi-dimensional image to 2D grayscale
    if img.ndim > 2:
        img = img[0] if img.shape[0] < img.shape[-1] else img[..., 0]

    masks, flows, _ = model.eval(img, diameter=None)
    return img, masks, flows

def run_cellpose_segmentation(input_path:str, output_path:str):
    """
    Function that segments all images in a folder using Cellpose

    params:
    input_path:str  | path to folder containing input images
    output_path:str | path to folder where masks will be saved
    """
    # Check GPU availability
    use_gpu = torch.cuda.is_available()
    model = models.CellposeModel(model_type='cyto3', gpu=use_gpu)

    # List input images
    filenames = sorted([f for f in os.listdir(input_path) if f.lower().endswith(('.tif', '.tiff'))])
    filepaths = [os.path.join(input_path, f) for f in filenames]

    os.makedirs(output_path, exist_ok=True)

    for image_path, filename in tqdm(zip(filepaths, filenames), total=len(filenames), desc="Running Cellpose"):
        img, masks, flows = segment_with_cellpose(image_path, model)
        out_path = os.path.join(output_path, filename)
        io.save_masks(img, masks, flows, out_path)

#########################################
# Define main function
def main() -> None:
    """
    Code's main function
    """
    parser = ArgumentParser()

    parser.add_argument("-i", "--input",
                        action="store",
                        dest="input_path",
                        required=True,
                        help="Path to folder containing input TIFF images.")
    
    parser.add_argument("-o", "--output",
                        action="store",
                        dest="output_path",
                        required=True,
                        help="Path to folder where segmented masks will be saved.")

    args = parser.parse_args()

    run_cellpose_segmentation(args.input_path, args.output_path)

    print("Cell segmentation complete!")

#########################################
# Execute if run directly
if __name__ == "__main__": main()
