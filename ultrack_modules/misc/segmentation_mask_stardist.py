"""
Module that receives a video and exports a segmentation mask using stardist
"""
####################################
from argparse import ArgumentParser

from dask.array.image import imread
from dask.array.core import Array

from os.path import join

from skimage.io import imsave

from ultrack.imgproc import normalize
from ultrack.utils.array import array_apply

from stardist.models import StarDist2D

from numpy import zeros_like
from numpy import int32
import numpy as np

####################################
# Define Argument Parsing Function

def get_args_dict() -> dict:
    """
    Function that reads the cli arguments and returns
    a dict containing them.
    :return: dict | Dictionary with cli passed arguments
    """
    parser = ArgumentParser(description="Module that receives a video and exports a segmentation mask using stardist")
    parser.add_argument("-i", "--input", required=True, help="Folder where the cell images are stored")
    parser.add_argument("-o", "--output", required=True, help="Folder to save the segmentation masks")
    return vars(parser.parse_args())

####################################
# Defining helper functions

def save_images(image:Array, name="Image", block_info = None, **kwargs) -> Array:
    filename = name + "-".join(map(str, block_info[0]["chunk-location"])) + ".tif"
    imsave(join(kwargs.get("folder"), filename), image)
    return image

def segment_photo(image: Array, model: StarDist2D) -> np.ndarray:
    """
    Receives a Dask Array (a block), converts it to NumPy, segments it, and returns NumPy result.
    """
    image_np = image.compute()  # Convert block to NumPy
    frame = normalize(image_np, gamma=2.0)
    labels, _ = model.predict_instances_big(
        frame, "YX", block_size=560, min_overlap=96, show_progress=False,
    )
    return labels.astype(np.int32)

def segment_array(video:Array) -> Array:
    model = StarDist2D.from_pretrained("2D_versatile_fluo")
    stardist_labels = zeros_like(video, dtype=int32)

    array_apply(
        video,
        out_array=stardist_labels,
        func=segment_photo,
        model=model,
    )
    
    return stardist_labels

####################################
# Defining main function
def main() -> None:
    args_dict = get_args_dict()
    input_folder    = args_dict["input"]
    output_folder   = args_dict["output"]
    
    input_video = imread(join(input_folder, "*"))
    
    segmentation_masks = segment_array(video=input_video)
    
    segmentation_masks.map_blocks(save_images, dtype=segmentation_masks.dtype, folder=output_folder).compute()

####################################
if __name__ == "__main__":
    main()
