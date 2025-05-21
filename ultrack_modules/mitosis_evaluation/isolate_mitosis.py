"""
Module that receives a ultrack tracking table and returns only
the last frame from a parent cell (mitosis frame)
"""

####################################
print("Importing required libraries...")
from argparse import ArgumentParser

from pandas import DataFrame
from pandas import read_csv

from numpy import delete, where
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
    description = "Module that receives a ultrack tracking table and returns only the last frame from a parent cell (mitosis frame)"
    
    # creating a parser instance
    parser = ArgumentParser(description=description)
    
    # adding arguments to parser
    parser.add_argument("-i", "--input_table",
                        action="store",
                        required=True,
                        dest="input",
                        help="Ultrack table (.csv)")

    parser.add_argument("-o", "--output_table",
                        action="store",
                        required=True,
                        dest="output",
                        help="Mitosis table (.csv)")
    
    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

####################################
# Defining helper functions

def isolate_mitosis(table:DataFrame) -> DataFrame:
    """
    Function that filters mitosis frames and position in
    utlrack dataframe

    :param table: pandas.DataFrame | ultrack table
    :return: pandas.DaraFrame | mitosis table
    """

    # Define parents list
    parents = table["parent_track_id"].unique()

    # Remove -1 index
    parents = delete(parents, where(parents == -1))

    # Create dict to create dataframe
    data_dict = {"track_id" : parents,
                 "t" : [],
                 "x" : [],
                 "y" : []}

    # populate dict for each parent
    for parent in parents:
        parent_data = table[table["track_id"] == parent]

        max_t = parent_data["t"].max()

        mitosis_data = parent_data[parent_data["t"] == max_t]

        if len(mitosis_data) > 0:

            data_dict["t"].append(max_t)
            data_dict["x"].append(mitosis_data["x"].item())
            data_dict["y"].append(mitosis_data["y"].item())

    mitosis_table = DataFrame(data=data_dict)

    return mitosis_table

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
    input_path  = args_dict["input"]
    output_path = args_dict["output"]

    # Open table
    input_table = read_csv(input_path)

    # Call mitosis function
    mitosis_table = isolate_mitosis(table = input_table)

    # Save table
    mitosis_table.to_csv(output_path, index=False)

    print("Done!")
    

####################################
if __name__ == "__main__":
    main()

# End of current module
