"""
Module that given a ultrack table creates a table for tracking validation
"""

######################################
# imports

from pandas import DataFrame, read_csv

######################################
# Define helper functions

def create_validators_table(input:DataFrame) -> DataFrame:
    """
    Function that creates a table for tracking validation
    from ultrack output csv.
    """

    validators_table = input.groupby("track_id").max()

    validators_table.drop(validators_table.columns.difference(["track_id", "t", "fate"]),axis= 1, inplace=True)

    return validators_table.reset_index()

######################################
# Define main function

def main() -> None:
    """
    Code's main function
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(description="")

    parser.add_argument("-i", "--input",
                        action="store",
                        required=True,
                        dest="input",
                        help="Ultracks output .csv")
    
    parser.add_argument("-o", "--output",
                        action="store",
                        required=True,
                        dest="output",
                        help="Table for validators (.csv)")
    
    args_dict = vars(parser.parse_args())

    input = read_csv(args_dict["input"])

    validators_table = create_validators_table(input)

    validators_table.to_csv(args_dict["output"], index=False)


######################################
# Call main function id runned directly
if __name__ == "__main__":
    main()

# end of current module-