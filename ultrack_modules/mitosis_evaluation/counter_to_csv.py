"""
Module that converts imagej cell counter output to csv with columns:
name, t, x, y
"""
####################################
# Imports
from argparse import ArgumentParser
import xml.etree.ElementTree as ET

from pandas import DataFrame

####################################
# Define argument parsing function
def get_args_dict() -> dict:
    """
    Parses the cl arguments into a dict
    :return: dict. Represent parsed arguments
    """

    # define program description
    description = "Convert CellCounter xml file to .csv"

    # Creating ArgumentParser instance
    parser = ArgumentParser(description=description)

    # Add arguments
    parser.add_argument("-i", "--input_file", "--counter_file",
                        dest="counter_file",
                        required=True,
                        help="Defines path to CellCounter file (.xml)")

    parser.add_argument("-o", "--output_file", "--output_table",
                        dest="output_path",
                        required=True,
                        help="Defines path to converted table (.csv)")

    # Create args dictionary
    args_dict = vars(parser.parse_args())

    return args_dict


####################################
# Define helper functions
def counter_to_csv(xml_path:str) -> DataFrame:
    """
    Function that converts a xml file from imagej cellcounter to DataFrame

    :param xml_path:
    :return:
    """
    # Open file and get file root
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Get data mark
    data = root.find("Marker_Data")

    # create_dataframe
    counter_dict = {"name" : [],
                    "t": [],
                    "x" : [],
                    "y" : []}

    # iterate over marker types in data
    for type in data.findall("Marker_Type"):
        # get data type name
        name = type.find("Name").text

        if " " in name:
            name = name.replace(" ", "_")

        for marker in type.findall("Marker"):
            counter_dict["name"].append(name)
            counter_dict["x"].append(marker.find("MarkerX").text)
            counter_dict["y"].append(marker.find("MarkerY").text)
            counter_dict["t"].append(int(marker.find("MarkerZ").text) - 1)

    counter_df = DataFrame(data=counter_dict)

    return counter_df


####################################
# Define main function
def main() -> None:
    """
    Code's main function
    :return: None
    """
    # Get cli passed arguments
    args_dict = get_args_dict()

    # Assign arguments to variables
    counter_file = args_dict["counter_file"]
    output_path = args_dict["output_path"]

    # Call main function
    output_df = counter_to_csv(xml_path=counter_file)

    # save dataframe
    output_df.to_csv(output_path, index=False)

####################################
# Cal main function
if __name__ == '__main__':
    main()
    print("Done!")
