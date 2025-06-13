"""
Python model
"""

######################################
# imports
from pandas import DataFrame, read_csv

######################################
# Define helper functions

def add_fate_to_ultrack_table(ultrack_table : DataFrame) -> DataFrame:
    """
    Function that adds detected cell fate to all cells in ultrack table

    params:
    ultrack_table : DataFrame | Ultrack dataframe to be added

    return : DataFrame | Ultrack DataFrame with fate collumn added
    """
    
    new_table = ultrack_table

    # Get max_frame
    max_frame = ultrack_table.t.max()
    
    # get parent_ids
    parent_ids = ultrack_table[ultrack_table["track_id"].isin(ultrack_table["parent_track_id"])].track_id.unique()

    last_frame_ids = new_table[new_table["t"] == max_frame].track_id.unique()

    for id in ultrack_table.track_id.unique():
        if id in parent_ids:
            new_table.loc[new_table.track_id == id, "fate"] = "mitosis"
        elif id in last_frame_ids:
            new_table.loc[new_table.track_id == id, "fate"] = "lived"
        else:
            new_table.loc[new_table.track_id == id, "fate"] = "death"

    return new_table

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
                        help="Ultrack table (.csv)")
   
    parser.add_argument("-o", "--output",
                        action="store",
                        dest="output",
                        required=False,
                        default="",
                        help="Output path (optional), if not set will overwrite original file")

    args_dict = vars(parser.parse_args())

    input_df = read_csv(args_dict["input"])

    output_df = add_fate_to_ultrack_table(input_df)

    save_path = args_dict["output"] if args_dict["output"] else args_dict["input"]
    
    output_df.to_csv(save_path, index = False)


######################################
# Call main function id runned directly
if __name__ == "__main__":
    main()

# end of current module
