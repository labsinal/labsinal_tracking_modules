"""
Module that aligns a image sequence with ultrack image aligner
"""
####################################
print("Importing required libraries...")
from argparse import ArgumentParser
from dask.array.image import imread
from dask.array.core import Array
from dask.array import from_zarr
from skimage.io import imsave
from os.path import join
from os import makedirs, listdir
from ultrack.imgproc import register_timelapse

print("All libraries imported sucessfully!")

####################################
# Define Argument Parsing Function

def get_args_dict() -> dict:
    """
    Function that reads the cli arguments and returns
    a dict containing them.
    :return: dict | Dictionary with cli passed arguments
    """
    
    # defining program description
    description = "Module that aligns image sequence"
    
    # creating a parser instance
    parser = ArgumentParser(description=description)
    
    # adding arguments to parser
    parser.add_argument("-i", "--input_folder",
                        action="store",
                        required=True,
                        dest="input_folder",
                        help="Folder containing unaligned images")

    parser.add_argument("-o", "--output_folder",
                        action="store",
                        required=True,
                        dest="output_folder",
                        help="Folder to contain aligned images")
    
    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

####################################
# Defining helper functions

def save_dask_image(image:Array,block_info = None, **kwargs) -> Array:
    """
    Function that saves a dask image
    :image: dask.Array | a dask image
    :output: str | path to folder to contain the dir
    :prefix: str | prefix for image name
    :return: dask.Array | same array as input
    """
    # create file name for the image
    n_frame = block_info[0]["chunk-location"][0]
    filename = "aligned_" + f"{n_frame:06d}" + ".tif"

    # save image
    imsave(join(kwargs.get("output_dir"), filename), image)
    return image

####################################
# Defining main function
def main() -> None:
    """
    Code's main function.
    :return: None
    """

    # Getting cli arguments dict
    args_dict = get_args_dict()

    input_folder = args_dict["input_folder"]
    output_folder = args_dict["output_folder"]

    images = imread(join(input_folder, "*.tif"))

    aligned_images = register_timelapse(images)

    makedirs(output_folder, exist_ok=True)

    images_to_save = from_zarr(aligned_images)

    images_to_save.map_blocks(save_dask_image, dtype=images_to_save.dtype,
                           output_dir=output_folder).compute()
    
    print("Done!")
    

####################################
if __name__ == "__main__":
    main()

# End of current module
