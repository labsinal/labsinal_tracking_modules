"""
Module that given a ultrack table creates a table for tracking validation
"""

######################################
# imports

from pandas import DataFrame, read_csv

######################################
# Define helper functions

def create_validators_table(input: DataFrame) -> DataFrame:
    """
    Function that creates a table for tracking validation
    from ultrack output csv.
    """
    # Compute min and max t and get last fate
    t_min = input.groupby("track_id")["t"].min().rename("t_incial")
    t_max = input.groupby("track_id")["t"].max().rename("t_final")
    fate = input.groupby("track_id")["destino"].last()  # last known fate

    # Combine all
    validators_table = DataFrame({
        "t_min": t_min,
        "t_max": t_max,
        "fate": fate
    }).reset_index()

    return validators_table

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

    validators_table.to_excel(args_dict["output"], index=False)


######################################
# Call main function if run directly
if __name__ == "__main__":
    main()

# end of current module
