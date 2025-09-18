# Module to join several ultrack output CSVs from the same video

######################################################################

# Import libraries
print("Importing Libraries...")
from os import listdir
from os.path import join
from pandas import DataFrame, read_csv
from src.aux_funcs import enter_to_continue, print_execution_parameters, print_progress_message
from src.tracking.ultrack.misc.tables.join_ultrack import join_tables
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
    description = "join all ultrack tables in a folder"

    # creating a parser instance
    parser = ArgumentParser(description=description)

    # adding arguments to parser

    parser.add_argument("-i", "--input",
                        action="store",
                        required=True,
                        dest="input_path",
                        help="Path to the folder with the ultrack outputs")
    
    parser.add_argument("-o", "--output",
                        action="store",
                        required=True,
                        dest="output_path",
                        help="Name of the csv file with all tables joined")

    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

######################################################################

# Define function

def join_tables_list(tables:list[DataFrame]) -> DataFrame:
    """
    Function that receives a tables_list with several ultrack outputs from batches
    from the same video and returns a DataFrame with all csvs data together
    :tables: list | List with DataFrames
    :return: DataFrame | table with the joined data from the tables list
    """

    # Current file = first file in the folder
    current = tables[0]

    # for each file in the folder join current with the next one
    for index, i in enumerate(tables[1:]):
        print_progress_message("Joining trackings: ", index, len(tables[1:]))
        current = join_tables(current, i)

    return current

######################################################################
# Define main function

def main() -> None:
    """
    Module main function
    :return: None 
    """
    # Get arguments
    args_dict = get_args_dict()
    
    # Assign arguments to variables
    input_path = args_dict["input_path"]
    output_path = args_dict["output_path"]
    
    # Print execution parameters and wait user response
    print_execution_parameters(args_dict)
    enter_to_continue()
    
    # Get a list of files in order
    files = list(map(lambda x : join(input_path, x), sorted(listdir(input_path))))

    # open all files
    tables = list(map(read_csv, files))
        
    # Join tables
    joined_data = join_tables_list(tables=tables)
    
    # Export data
    joined_data.to_csv(output_path, index=False)    
    
    
######################################################################
# Call main function
if __name__ == "__main__":
    main()
