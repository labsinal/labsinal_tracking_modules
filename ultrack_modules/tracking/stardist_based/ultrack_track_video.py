"""
Module that tracks a video and exports its tracking table
"""
####################################
print("Importing required libraries...")
from argparse import ArgumentParser

from ultrack.utils import estimate_parameters_from_labels, labels_to_contours
from ultrack.config.config import MainConfig
from ultrack import load_config, track, to_tracks_layer
from ultrack.tracks import close_tracks_gaps
from ultrack.imgproc import tracks_properties

from matplotlib.pyplot import show

from dask.array.image import imread
from dask.array.core import Array
from pandas import DataFrame

from misc.segmentation_mask_stardist import segment_array

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
    description = "Module that tracks a video and exports its tracking table"
    
    # creating a parser instance
    parser = ArgumentParser(description=description)
    
    # adding arguments to parser
    parser.add_argument("-i", "--input",
                        action="store",
                        required=True,
                        dest="input",
                        help="Input folder with segmentation masks to be tracked")

    parser.add_argument("-o", "--output",
                        action="store",
                        required=True,
                        dest="output",
                        help="Output file to save tracking output (.csv)")
    
    parser.add_argument("-c", "--config",
                        action="store",
                        required=False,
                        default="/home/frederico-mattos/Documents/UFRGS/labsinal/misc/ultrack_config.toml",
                        dest="config_file",
                        help="path to a config file")

    parser.add_argument("--areas_graph",
                        action="store_true",
                        required=False,
                        dest="make_graph",
                        help="Whether to make areas graph to tune configs")
    
    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

####################################
# Defining helper functions

def track_video(video:Array, config_file:str) -> DataFrame:
    """
    DESCRIPTION
    """
    
    # create labels
    labels = segment_array(video)
    
    # Create detection and edges
    detection, edges = labels_to_contours(labels, sigma=4.5) 
    
    # create config object
    config = load_config(config_file)
    
    # track the video
    track(
        detection=detection,
        edges=edges,
        config=config,
        overwrite=True,
    )
    
    # create tracks df
    tracks_df, _ = to_tracks_layer(config)
    
    # close tracks gaps
    print("[Using function close_tracks_gaps, to disable comment line 94!]")
    tracks_df = close_tracks_gaps(tracks_df, 50, 50, spatial_columns=["x", "y"])
    
    tracks_df_areas = tracks_properties(labels, image=video, tracks_df=tracks_df)
    
    # return tracks_df
    return tracks_df_areas

####################################
# Defining main function
def main() -> None:
    """
    Code's main function.
    :return: None
    """

    # Getting cli arguments dict
    args_dict = get_args_dict()
    
    # Assign cli arguments to variables
    input_folder    = args_dict["input"]
    config_file     = args_dict["config_file"]
    output_file     = args_dict["output"]
    make_graph      = args_dict["make_graph"]

    # Open segmentation mask
    segmentation_video = imread(input_folder + "/*")
    
    # if make graph is true, make the graph and exit function
    if make_graph:
        params_df = estimate_parameters_from_labels(segmentation_video, is_timelapse=True)
        params_df["area"].plot(kind="hist", bins=100, title="Area histogram")
        show()
        return
    
    # else, track the video
    output_df = track_video(video=segmentation_video, config_file=config_file)
    
    output_df.to_csv(output_file, index=False)
    
    print("Done!")
    

####################################
if __name__ == "__main__":
    main()

# End of current module
