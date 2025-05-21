"""
Module that converts an Ultrack output table to a clovars input table
"""
####################################
print("Importing required libraries...")
from argparse import ArgumentParser


from pandas import read_csv
from pandas import DataFrame
from math import sqrt
from math import pi
from numpy import ndarray
from numpy import append
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
    description = "Code that converts a ultrack output table to a clovars like format"
    
    # creating a parser instance
    parser = ArgumentParser(description=description)
    
    # adding arguments to parser
    parser.add_argument("-i", "--input",
                        action="store",
                        required=True,
                        dest="input_table",
                        help="Path to a table from ultrack (.csv)")

    parser.add_argument("-o", "--output",
                        action="store",
                        required=True,
                        dest="output_path",
                        help="Path to save the clovars_like table (.csv)")
    
    parser.add_argument("-t", "--time_interval",
                        action="store",
                        required=False,
                        type=float,
                        default=30,
                        dest="time_interval",
                        help="Time interval between frames")
    
    parser.add_argument("-c", "--colony_name",
                        action="store",
                        required=False,
                        default="1a",
                        dest="colony_name",
                        help="Name of the colony")

    parser.add_argument("--treatment_name",
                        action="store",
                        required=False,
                        default="None",
                        dest="treatment_name",
                        help="Treatment used in the colony")
    
    
    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

####################################
# Defining helper functions

def convert_time_related_columns(input_table:DataFrame,
                                 time_interval:float) -> None:
    """
    Function that converts time related columns from a 
    ultrack table to a clovars-like table
    :input_table: DataFrame | table from ultrack
    :time_interval: float | Time between frames
    :return: None, it edits the input table
    """
    # seconds
    input_table["simulation_seconds"] = input_table["t"] * time_interval * 60
    # hours
    input_table["simulation_hours"] = input_table["t"] * time_interval / 60
    # days
    input_table["simulation_days"] = input_table["simulation_hours"] / 24
    # rename frames
    input_table = input_table.rename(columns={"t":"simulation_frames"})

    return input_table
    
def fix_branch_name_generation(table:DataFrame, index:int, generation = 0) -> None:
    """
    Function that receives a tracking df and a root cell index
    and modifies the table to fill, generation, name and branch name
    columns in CloVarS format
    :table: DataFrame | trackings df
    :index: int | root cell track_id
    :generation: int | default = 0 | generation of index cell
    :return: None 
    """
    children = table.loc[table["parent_track_id"] == index, "track_id"].unique()
    if any(children):
        for i, item in enumerate(children):
            # fix generation
            table.loc[table["track_id"] == item, "generation"] = generation+1
            
            # fix branch name
            branch_name = table[table["track_id"] == index].get("branch_name").unique()[0]
            table.loc[table["track_id"] == item, "branch_name"] = branch_name
            
            # fix name
            name = table[table["track_id"] == index].get("name").unique()[0] + f".{i+1}"
            table.loc[table["track_id"] == item, "name"] = name
            
            table = fix_branch_name_generation(table, item, generation=generation+1)
    return table

def ultrack_to_clovars(input_table:DataFrame,
                       time_interval:float,
                       colony_name:str,
                       treatment_name:str) -> DataFrame:
    """
    Function that converts and ultrack output table to a
    clovars like table format
    :input_table: DataFrame | table from ultrack
    :time_interval: float | time between frames (minutes)
    :return: DataFrame | converted table
    """
    # resolve time related columns
    input_table = convert_time_related_columns(input_table, time_interval)
    
    # Resolve cli passed arguments and constant values
    input_table["colony_name"] = colony_name
    input_table["treatment_name"] = treatment_name
    input_table["signal_value"] = 0
    
    # Resolve branch_name, generation and name
    root_ids = input_table.loc[input_table["parent_track_id"] == -1, "track_id"].unique()
    
    input_table["name"] = ""
    input_table["generation"] = -1   
    input_table["branch_name"] = ""

    for index, item in enumerate(root_ids):
        branch_name = colony_name + "-" + str(index+1)
        
        input_table.loc[input_table["track_id"] == item, "branch_name"] = branch_name
        input_table.loc[input_table["track_id"] == item, "name"] = branch_name
        input_table.loc[input_table["track_id"] == item, "generation"] = 0
        
        
        input_table = fix_branch_name_generation(table=input_table,index=item)
        
    # Resolve seconds_since_birth
    input_table["seconds_since_birth"] = 0
    
    
    # Iterate over each cell assigning current second - birth second to
    # seconds since birth
    for id in input_table["track_id"].unique():
        
        birth_second = min(input_table.loc[input_table["track_id"] == id, 
                                           "simulation_seconds"])
        input_table.loc[input_table["track_id"] == id, 
                        "seconds_since_birth"] = input_table["simulation_seconds"] - birth_second
    
    # Resolve fate at next frame
    
    # define default value
    input_table["fate_at_next_frame"] = "migration"

    # create variables for the last and current frame
    max_frame = max(input_table["simulation_frames"])
    current_frame = 0
    # create variable for current frame track_ids
    current_ids = input_table.loc[input_table["simulation_frames"] == current_frame, "track_id"].unique()
    
    while current_frame < max_frame:
        # discover track_ids from the next frame
        next_ids = input_table.loc[input_table["simulation_frames"] == current_frame+1, "track_id"].unique()
        
        # iterate over current ids
        for id in current_ids:
            # if current frame id is not in the next frame
            if id not in next_ids:
                # check if it is a parent
                parent_track_ids = input_table["parent_track_id"].unique()
                # if it is not a parent, it is dead
                if id not in parent_track_ids:
                    input_table.loc[(input_table["simulation_frames"] == current_frame)  &
                                    (input_table["track_id"] == id), 
                                    "fate_at_next_frame"] = "death"
                # if it is, it is dividing
                else:
                    input_table.loc[(input_table["simulation_frames"] == current_frame)  &
                                    (input_table["track_id"] == id), 
                                    "fate_at_next_frame"] = "division"
        # increment current frame
        current_frame += 1
        # make current ids <- next ids
        current_ids = next_ids.copy()
    
    # filter only wanted
    input_table = input_table.drop(['parent_id', 'parent_track_id', 'id'], axis=1)
    
    #Define better collumn order
    columns_titles = ["id","name",
                  "branch_name","colony_name",
                  "generation",
                  "x", "y", "area",
                  "signal_value",
                  "seconds_since_birth",
                  "fate_at_next_frame",
                  "treatment_name",
                  "simulation_frames",
                  "simulation_seconds","simulation_hours",
                  "simulation_days"]
    input_table = input_table.rename(columns={"track_id":"id"})
    input_table = input_table.reindex(columns=columns_titles)
    
    return input_table
    
    
####################################
# Defining main function
def main() -> None:
    """
    Code's main function.
    :return: None
    """

    # Getting cli arguments dict
    args_dict = get_args_dict()
    
    # Assigning cli arguments to variables
    input_path      = args_dict["input_table"]
    output_path     = args_dict["output_path"]
    time_interval   = args_dict["time_interval"]
    colony_name     = args_dict["colony_name"]
    treatment_name   = args_dict["treatment_name"]
    
    # Open input table
    input_table = read_csv(input_path)
    
    # Convert table
    converted_table = ultrack_to_clovars(input_table = input_table,
                                         time_interval = time_interval,
                                         colony_name=colony_name,
                                         treatment_name=treatment_name)
    
    # Export table
    converted_table.to_csv(output_path, index=False)
    
    print("Done!")
    

####################################
if __name__ == "__main__":
    main()

# End of current module
