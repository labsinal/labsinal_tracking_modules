"""
Module that converts beatriz's icy data anotation to mitosis.csv
"""

# Imports
from pandas import DataFrame

#####################################
# Define helper functions

def bea_to_mitosis_csv(bea:DataFrame) -> DataFrame:
    """
    Function that converts bea's annotation format to mitosis.csv

    params:
    bea : pandas.DataFrame | DataFrame in bea's annotation format
    return : DataFrame | DataFrame in the mitosis.csv format
    """
    


#####################################
# Define main function

def main() -> None:
    """
    Code's main function
    """
    # import argument parser
    from argparse import ArgumentParser

    # initialize argument parser
    parser = ArgumentParser(description="Module that converts beatriz's icy data anotation to mitosis.csv")

    # add arguments
    parser.add_argument("-i", "--input", "--bea-data",
                        action="store",
                        required=True,
                        dest="input",
                        help="Bea's annotation format file (.excel)")
    
    parser.add_argument("-o", "--output",
                        action="store",
                        dest="output",
                        required=True,
                        help="File in the mitosis.csv format to be saved (.csv)")
    
    # create args dict
    args_dict = vars(parser.parse_args())

####################################
# Run main function if runned direclty
if __name__ == "__main__": 
    main()