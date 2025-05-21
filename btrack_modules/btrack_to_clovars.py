# Convert tables from btrack output format to CloVarS format

######################################################################

# importing libraries
print("Importing Libraries...")
from pandas import DataFrame
from pandas import read_csv
from argparse import ArgumentParser
print("All libraries imported!")

######################################################################
# argument parsing related functions

def get_args_dict() -> dict:
    """
    Parses the arguments and returns a dictionary of the arguments.
    :return: Dictionary. Represents the parsed arguments.
    """
    # defining program description
    description = "Convert csv from btrack output to clovars format"

    # creating a parser instance
    parser = ArgumentParser(description=description)

    # adding arguments to parser

    parser.add_argument("-i", "--input",
                        action="store",
                        required=True,
                        dest="input_path",
                        help="Path to the btrack csv")

    parser.add_argument("-o", "--output",
                        action="store",
                        required=True,
                        dest="output_path",
                        help="Path to the output (CloVarS) csv")

    parser.add_argument("-t", "--time_interval",
                        type=float,
                        action="store",
                        required=True,
                        dest="time_interval",
                        help="Time in minutes between frames")

    parser.add_argument("-m", "--only_mitosis", "--mitosis",
                        action="store_true",
                        required=False,
                        dest="only_mitosis",
                        help="Filter only branches with more than one cell")

    parser.add_argument("--colony", "--colony_name",
                        action="store",
                        required=False,
                        default="1a",
                        dest="colony_name",
                        help="Name of the cell colony")

    parser.add_argument("--treatment","--treatment_name", 
                        action="store",
                        required=False,
                        default="Control",
                        dest="treatment_name",
                        help="Name of the treatment used in the colony")


    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

################################################################
#Defining other functions

def get_branches(data:DataFrame) -> list:
    """
    Function that return a list with lists containing all ids of cell mutually related
    in the dataframe
    :data: dataframe with tracking data
    :return: List of branches
    """
    branches = []
    data.sort_values("simulation_frames")
    for i, id in enumerate(data["id"].unique()):
        cell_data = data[data["id"] == id]
        is_in = False
        for branch in branches:
            if min(cell_data["parent"].unique()) in branch: 
                branch.append(id)
                is_in = True
                break
        if not is_in:
            branches.append([id])
    print("Got branches...")
    return branches

def btrack_to_clovars(input_path:str,
                      time_interval:float,
                      only_mitosis:bool,
                      colony_name:str,
                      treatment_name:str) -> DataFrame:
    """
    Function that converts a btrack output csv to a csv in clovars format
    :input_path: Path to the btrack input
    :only_mitosis: If the code will filter branches with more than one cell
    :colony_name: Name of the cell colony
    :treatment_name: Name of the treatment used in the colony
    :return: converted df
    """

    data = read_csv(input_path, sep= " ")
    
    print("Simple cases...")
    
    ## Solve simple cases, such as type conversion and change names
    data["generation"] = list(map(int, (data["generation"])))
    data["t"] = list(map(int, (data["t"])))
    data = data.rename(columns={"ID": "id", "t": "simulation_frames"})
    
    ## Solve cases where collumn have a constant value
    data.insert(0, "colony_name", colony_name)
    data.insert(0, "signal_value", 0.0)
    data.insert(0, "treatment_name", treatment_name)

    # Solve columns related to time
    frame_interval = time_interval
    data["simulation_seconds"] = data["simulation_frames"]*frame_interval*60
    data["simulation_hours"] = data["simulation_seconds"]/3600
    data["simulation_days"] = data["simulation_hours"]/24

    print("DONE")

    #HARDER CASES
    
    print("Seconds since birth...")
    # seconds_since_birth
    # Primeiro criar "frame_since_birth" e converter pra segundos
    data.insert(0, "frame_since_birth", 0)
    for id in data["id"].unique():
        min_frame = min(data[data["id"] == id]["simulation_frames"])
        data.loc[data["id"] == id, "frame_since_birth"] = data["simulation_frames"] - min_frame

    data["seconds_since_birth"] = data["frame_since_birth"]*frame_interval*60
    
    print("branch name...")
    # branch name
    branches = get_branches(data)

    for branch_index, branch in enumerate(branches):
        for id_index, id in enumerate(branch):
            branch_name = colony_name + "-" + str(branch_index+1)
            data.loc[data["id"] == id, "branch_name"] = branch_name
            
            value = id_index
            while True:
                if value == 0:
                    data.loc[data["id"] == id, "name"] = branch_name
                    break
                elif value <= 2:
                    cell_data = data.loc[data["id"] == id]
                    parent = min(cell_data["parent"])
                    data.loc[data["id"] == id, 
                             "name"] = data.loc[data["id"] == parent, 
                                                "name"].iloc[0] + "."+str(value)
                    break
                else:
                    value -= 2

    print("fate...")
    # fate at next frame
    data.insert(0, "fate_at_next_frame", "migration")
    last_frame = max(data["simulation_frames"])

    for id in data["id"].unique():
        cell_last_frame = max(data.loc[data["id"] == id, "simulation_frames"])
        
        if cell_last_frame == last_frame: continue
            
        if id in data.loc[data["simulation_frames"] == cell_last_frame+1, 
                          "parent"].unique():
            data.loc[(data["id"] == id) & (data["simulation_frames"] == cell_last_frame),
                     "fate_at_next_frame"] = "division"
            continue
        else:
            data.loc[(data["id"] == id) & (data["simulation_frames"] == cell_last_frame), 
                     "fate_at_next_frame"] = "death"
    
            
    #Drop unwanted cols
    data = data.drop(["parent", "frame_since_birth", "root", "state", "dummy", ], axis=1)
    
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

    data = data.reindex(columns=columns_titles)

    if only_mitosis:
        #Filter for only branches with more than one cell
        filtered_branches = list(filter(lambda x:len(x) == 1, branches))
        drop_ids = [item for sublist in filtered_branches for item in sublist]
        drop_indexes = []
        for id in drop_ids:
            drop_indexes.extend(data.index[data["id"] == id].tolist())

        data = data.drop(drop_indexes, axis= 0)
    
    return data

################################################################
# Defining main function
def main() -> None:
    """
    Main function
    :return: None
    """
    #Getting arguments dict
    args_dict = get_args_dict()
    
    #Defining the input path
    input_path = args_dict["input_path"]
    #Defining the output path
    output_path = args_dict["output_path"]
    #Defining time interval
    time_interval = args_dict["time_interval"]
    #Defining only mitosis filter
    only_mitosis = args_dict["only_mitosis"]
    #Defining Colony name
    colony_name = args_dict["colony_name"]
    #defining treatment_name
    treatment_name = args_dict["treatment_name"]
    
    print("Converting data...")
    
    converted_data = btrack_to_clovars(input_path = input_path,
                                       time_interval=time_interval,
                                       only_mitosis=only_mitosis,
                                       colony_name=colony_name,
                                       treatment_name=treatment_name)
    
    print("Data successfully converted.")
    
    print("Saving data")
    # Save data
    converted_data.to_csv(output_path)
    print("Data successfully saved.")

##############################################################
# Running the code
if __name__ == "__main__":
    main()
