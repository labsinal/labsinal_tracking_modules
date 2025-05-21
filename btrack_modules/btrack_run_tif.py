# Code that runs btrack tracking

##########################################
# Imports

print("Importing required libs...")
import btrack
from btrack.dataio import export_CSV
from skimage.io import imread
from argparse import ArgumentParser

##########################################
# argument parsing related functions

def get_args_dict() -> dict:
    """
    Parses the arguments and returns a dictionary of the arguments.
    :return: Dictionary. Represents the parsed arguments.
    """
    # defining program description
    description = "Module that runs btrack, exports its output to csv"

    # creating a parser instance
    parser = ArgumentParser(description=description)

    # adding arguments to parser

    parser.add_argument("-i", "--input",
                        action="store",
                        required=True,
                        dest="input_file",
                        help="Path to the input file (animated tif)")

    parser.add_argument("-c", "--config",
                        action="store",
                        required=True,
                        dest="config_file",
                        help="Path to the config file (.json)")

    parser.add_argument("-o", "--output",
                        action="store",
                        required=True,
                        dest="output_file",
                        help="Path to the output file (csv)")
    
    # create args dict
    args_dict = vars(parser.parse_args())
    
    return args_dict


##########################################
# defining auxiliary functions

def run_btrack(segmentation_file:str, config:str, output:str) -> None:
    """
    Function that runs the btrack tracking
    :segmentation_file: path to a .tif file containing the cells segmentation
    :config: path to the btrack config file
    :output: path to the output csv
    """
    # load your segmentation data
    segmentation = imread(segmentation_file)

    # create btrack objects (with properties) from the segmentation data
    # (you can also calculate properties, based on scikit-image regionprops)
    objects = btrack.utils.segmentation_to_objects(
    segmentation, properties=('area', )
    )

    print("SEGMENTATION LOADED ---------------------------------------------------------------------")

    # initialise a tracker session using a context manager
    with btrack.BayesianTracker() as tracker:

        # configure the tracker using a config file
        tracker.configure(config)

        # append the objects to be tracked
        tracker.append(objects)
        
        # set the volume (Z axis volume limits default to [-1e5, 1e5] for 2D data)
        tracker.volume = ((0, 1200), (0, 1600))

        # track them (in interactive mode)
        tracker.track_interactive(step_size=100)

        print("OPTIMIZING --------------------------------------------------------------------")

        # generate hypotheses and run the global optimizer
        tracker.optimize()

        # get the tracks as a python list
        tracks = tracker.tracks

        # store the data in an csv file
        export_CSV(filename=output, tracks=tracks)
    
##########################################
# Creating main function

def main() -> None:
    """
    Main function that runs the code
    :return: None
    """
    # get args dict
    args_dict = get_args_dict()
    
    # parse args
    input_file = args_dict["input_file"]
    config_file = args_dict["config_file"]
    output = args_dict["output_file"]
    
    print("Running btrack")
    
    run_btrack(segmentation_file=input_file,
               config=config_file,
               output=output)
    
    print("File saved")

##########################################
# Calling main function

if __name__ == "__main__":
    main()

# End of the module
