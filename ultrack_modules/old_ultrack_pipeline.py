"""
Complete tracking pipeline using ultrack
input = cell video
output = tracking.csv
"""
####################################
print("Importing required libraries...")
from argparse import ArgumentParser

from ultrack.imgproc import register_timelapse

from skimage.io import imsave

from dask.array.image import imread
from dask.array.core import Array
from dask.array import from_zarr

from os.path import join
from os import makedirs

from src.aux_funcs import print_execution_parameters, enter_to_continue
from src.tracking.ultrack.tracking.ultrack_track_video import track_video

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
    description = "Complete tracking pipeline using ultrack"
    
    # creating a parser instance
    parser = ArgumentParser(description=description)
    
    # adding arguments to parser
    parser.add_argument("-i", "--input",
                        action="store",
                        required=True,
                        dest="input",
                        help="Folder with cell video images")
    
    parser.add_argument("-o", "--output",
                        action="store",
                        required=True,
                        dest="output",
                        help="Folder folder to save output")

    parser.add_argument("-c", "--config_file",
                        action="store",
                        required=True, 
                        dest="config_file",
                        help="Path to ultrack configuration file")
    
    parser.add_argument("--save_aligned_images",
                        action="store_true",
                        required=False,
                        dest="save_aligned_images",
                        help="add this to save the aligned images")
    
    
    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

####################################
# Create global variables
SAVE_ALIGNED_IMAGES : bool = False

####################################
# Defining helper functions

def save_dask_image(image:Array, block_info = None,**kwargs) -> Array:
    """
    Function that saves a dask image
    :image: dask.Array | a dask image
    :output: str | path to folder to contain the dir
    :prefix: str | prefix for image name
    :return: dask.Array | same array as input
    """
    # create file name for the image
    n_frame = block_info[0]["chunk-location"][0]
    filename = kwargs.get("prefix") + "_" + f"{n_frame:06d}" + ".tif"
    
    # save image
    imsave(join(kwargs.get("output_dir"), filename), image)
    return image   
    

def tracking_pipeline(input_path:str, config_file:str ,output_path:str) -> None:
    """
    Complete tracking pipeline function, from video to tracking
    :input_path: str | path where the cell images are
    :output_path: str | path to save the output
    """
    
    # get acces to global variables
    global SAVE_ALIGNED_IMAGES
    
    # open images
    images : Array = imread(join(input_path, "*"))
    
    # register image
    aligned_images  = register_timelapse(images)
    
    # check cli argument
    if SAVE_ALIGNED_IMAGES:
        aligned_dir = join(output_path, "aligned_images")
        makedirs(aligned_dir, exist_ok=True)
        
        save_images = from_zarr(aligned_images)
        
        save_images.map_blocks(save_dask_image, dtype=save_images.dtype,
                                  output_dir = aligned_dir, prefix = "aligned").compute()
    
    # track
    tracking = track_video(video=aligned_images, config_file=config_file)

    # export
    tracking.to_csv(join(output_path, "tracking.csv"), index=False)
    

####################################
# Defining main function
def main() -> None:
    """
    Code's main function.
    :return: None
    """
    # get access to global variables
    global SAVE_ALIGNED_IMAGES

    # Getting cli arguments dict
    args_dict = get_args_dict()
    
    # assign cli arguments to variables
    input_path  = args_dict["input"]
    config_file = args_dict["config_file"]
    output_path = args_dict["output"]
    
    # edit global variables
    SAVE_ALIGNED_IMAGES = args_dict["save_aligned_images"]
    
    # cli interface
    print_execution_parameters(args_dict)
    enter_to_continue()
    
    # call pipeline function
    tracking_pipeline(input_path=input_path, config_file=config_file ,output_path=output_path)
    
    print("Done!")
    

####################################
if __name__ == "__main__":
    main()

# End of current module