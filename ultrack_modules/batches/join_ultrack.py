"""
Module that join two ultrack tables from subsequent batches
"""
####################################
print("Importing required libraries...")
from argparse import ArgumentParser

from pandas import read_csv, concat
from pandas import DataFrame
from src.aux_funcs import print_execution_parameters, enter_to_continue
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
    description = "Code that join two ultrack tables from subsequent batches"
    
    # creating a parser instance
    parser = ArgumentParser(description=description)
    
    # adding arguments to parser
    parser.add_argument("-f", "--first_table",
                        action="store",
                        required=True,
                        dest="first_table",
                        help="First table with the tracking data")

    parser.add_argument("-s", "--second_table",
                        action="store",
                        required=True,
                        dest="second_table",
                        help="second table with the tracking data")
    
    parser.add_argument("-o", "--output",
                        action="store",
                        required=True,
                        dest="output",
                        help="output_path")
    
    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

####################################
# Defining helper functions

def get_ids_mapper(first_last_frame:DataFrame,
                   second_first_frame:DataFrame) -> dict:
    """
    Function that create a dict linking:
    second_first_frame_track_id -> first_last_frame_track_id
    :second_first_frame: DataFrame | df containing data from the first frame
                                     from the second video
    :first_last_frame: DataFrame | df containing data from the last frame
                                   from the first video
    :return: dict | dictionary linking ids
    """
    # Create id's mapper
    ids_mapper = {}
    # Populate ids_mapper:
    # Iterate over cell in second video last frame
    for id in second_first_frame["track_id"]:
        # Get current cell data
        second_cell_data = second_first_frame[second_first_frame["track_id"] == id]
        x = second_cell_data["x"].item()
        y = second_cell_data["y"].item()

        # Find overlapping track in the first video
        first_cell_data = first_last_frame[(first_last_frame["x"] == x) & (first_last_frame["y"] == y)]
        
        # If there is a overlapping tracking map its id in the dict
        if len(first_cell_data["track_id"]) > 0:
            
            # Map id_from_second_video : id_from _first_video
            ids_mapper[id] = first_cell_data["track_id"].item()
    
    # Return filled mapper
    return ids_mapper

def join_tables(first:DataFrame, 
                second:DataFrame) -> DataFrame:
    """
    Function that join two tables from subsequent
    tracked batches
    :first: DataFrame | Data frame with first batch tracking data
    :second: DataFrame | Data frame with second batch tracking data
    :return: DataFrame | Data frame with both batches tracking data
    """
    # Check if there is a duplicate id column and drop it
    if "id.1" in first.columns:
        first = first.drop(labels="id.1", axis=1)
        second = second.drop(labels="id.1", axis=1)
    
    # Get the first batch last frame index
    last_frame_index = first["t"].max()
    
    # Get the last added id in the first video
    first_greatest_track_id = first["track_id"].max()
    
    # Adjust second DataFrame "t" and "id"
    second["t"] += last_frame_index
    second["id"] += last_frame_index*(10**6)
    
    # Adjust track_id so it doesn't repeat from the first video
    second["track_id"] += first_greatest_track_id
    
    # Get data from the overlapping frames from both video
    first_last      = first[first["t"] == last_frame_index]
    second_first    = second[second["t"] == last_frame_index]
    
    # Create dict linking track_id_second:track_id_first
    ids_mapper  = get_ids_mapper(first_last_frame=first_last,
                                 second_first_frame=second_first)

    for second_id, first_id in ids_mapper.items():
        # track_id
        second.loc[second["track_id"] == second_id, "track_id"] = first_id
        # parent_track_id
        second.loc[second["track_id"] == first_id, 
                "parent_track_id"] = first_last.loc[first_last["track_id"] == first_id, 
                                                    "parent_track_id"].item()
        # parent_id
        second.loc[(second["track_id"] == first_id) & (second["t"] == last_frame_index),
                                    "parent_id"] = first_last.loc[first_last["track_id"] == first_id,
                                                                "parent_id"].item()
    
    joined_df = concat([first[first["t"] != last_frame_index], second])
    
    return joined_df
    

####################################
# Defining main function
def main() -> None:
    """
    Code's main function.
    :return: None
    """

    # Getting cli arguments dict
    args_dict = get_args_dict()
    
    # Assign each argument to a variable
    first_path  = args_dict["first_table"]
    second_path = args_dict["second_table"]
    output_path = args_dict["output"]
    
    print_execution_parameters(args_dict)
    enter_to_continue()

    # Create input tables Dataframes
    first_table  = read_csv(first_path)
    second_table = read_csv(second_path)
    
    print("Joining Tables...")
    # Assign the joined tables to a variable
    joined_table = join_tables(first=first_table,
                               second=second_table)
    
    print("Exporting_data...")
    # Export joined table
    joined_table.to_csv(output_path, index=False)
    
    print("Done!")

####################################
if __name__ == "__main__":
    main()

# End of current module
