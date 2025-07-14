"""
Module that tracks a segmentation masks video and exports its tracking table
"""
####################################
from argparse import ArgumentParser


from pathlib import Path
from ultrack.utils import estimate_parameters_from_labels, labels_to_contours
from ultrack.config.config import MainConfig
from ultrack import load_config, track, to_tracks_layer
from ultrack.tracks import close_tracks_gaps
from ultrack.imgproc import tracks_properties
from ultrack.core.export import to_ctc

from matplotlib.pyplot import show

from dask.array.image import imread
from dask.array.core import Array
from pandas import DataFrame

from os.path import join

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
                        help="Output dir to save tracking output")
    
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

def track_segmentation(video:Array, config_file:MainConfig, output_dir:str) -> DataFrame:
    """
    Function that tracks a segmentation masks video
    :video: dask.Array | Array contaning the video data
    :config_file: str | path to the ultrack configuration file
    :return: pandas.DataFrame | tracks_df with tracking data 
    """ 
    # Create detection and edges
    detection, edges = labels_to_contours(video, sigma=4.5)
    
    # track the video
    track(
        detection=detection,
        edges=edges,
        config=config_file,
        overwrite=True,
    )
    
    # create tracks df
    tracks_df, _ = to_tracks_layer(config_file)
    
    # close tracks gaps
    print("[Using function close_tracks_gaps, to disable comment line 94!]")
    tracks_df = close_tracks_gaps(tracks_df, 50, 50, spatial_columns=["x", "y"])

    to_ctc(Path(output_dir),config_file)

    # return tracks_df
    return tracks_df

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

    conf_obj = load_config(config_file)

    # else, track the video
    tracks_df = track_segmentation(video=segmentation_video, config_file=conf_obj, output_dir=output_file)
    
    tracks_df.to_csv(join(output_file, "trackings.csv"))

    print("Done!")
    

####################################
if __name__ == "__main__":
    main()

# End of current module
