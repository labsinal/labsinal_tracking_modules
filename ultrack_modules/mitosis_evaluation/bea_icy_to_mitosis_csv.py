"""
Module that converts beatriz's icy data anotation to mitosis.csv
"""

# Imports
from pandas import DataFrame, read_excel

#####################################
# Define helper functions

def bea_to_mitosis_csv(bea:DataFrame) -> DataFrame:
    """
    Function that converts bea's annotation format to mitosis.csv

    params:
    bea : pandas.DataFrame | DataFrame in bea's annotation format
    return : DataFrame | DataFrame in the mitosis.csv format
    """

    # Filter only wanted cols
    output_df = bea[["Name", "Position X", "Position Y", "Position T"]]

    # Filter only mitosis detections
    output_df = output_df[output_df["Name"].str.contains("(mitosis)")]

    # Remove "(mitosis)"
    output_df.Name = output_df.Name.str.replace("(mitosis)", "")

    # Rename the collumns
    output_df = output_df.rename(columns={"Name" : "name", 
                              "Position X" : "x",
                              "Position Y" : "y",
                              "Position T" : "t"})

    return output_df

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
    args_dict : dict = vars(parser.parse_args())

    # Open bea's file
    input_df : DataFrame = read_excel(args_dict["input"])

    # Call function
    output_df : DataFrame = bea_to_mitosis_csv(input_df)

    # Save output df
    output_df.to_csv(args_dict["output"])

    print("Done!")

####################################
# Run main function if runned direclty
if __name__ == "__main__": 
    main()