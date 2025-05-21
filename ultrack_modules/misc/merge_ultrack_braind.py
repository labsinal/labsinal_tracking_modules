print("Importing libraries...")
from pandas import read_csv, DataFrame
from argparse import ArgumentParser

######################################

def get_args_dict() -> dict:
    """
    Parses the cl arguments into a dict
    :return: dict. Represent parsed arguments
    """
    
    # define program description
    description = "merge ultrack output data and braind output data"
    
    # Creating ArgumentParser instance
    parser = ArgumentParser(description=description)
    
    # Adding arguments
    
    # Input ultrack file path
    parser.add_argument("-u", "--ultrack_data",
                        dest="ultrack_data",
                        required=True,
                        help="Defines path to ultrack .csv output")
    
    # Input braind file path
    parser.add_argument("-b", "--braind_data",
                        dest="braind_data",
                        required=True,
                        help="Defines path to braind .csv output")

    # output file path
    parser.add_argument("-o", "--output",
                        dest="output_file",
                        required=True,
                        help="Defines path to program output")
    
    
    # Create args dictionary
    args_dict = vars(parser.parse_args())
    
    return args_dict

######################################


# Get args dict
args = get_args_dict()

# Open both files as two pandas df
u_db = read_csv(args["ultrack_data"])
b_db = read_csv(args["braind_data"])

# Create a frame collum in the braind df
    # Get a sorted list with the name of the image files
img_files = sorted(list(b_db['img_name'].unique()))
    # add to the frame collumn based on the sorted list index
b_db['frame'] = list(map(lambda x:img_files.index(x), b_db['img_name']))

# Merge both dataframes and drop duplicate collumns
m_db = u_db.merge(b_db,
                  left_on=["t", "x", "y"], 
                  right_on=["frame", "cx", "cy"]
                  ).drop(["cx", "cy", 'frame'],
                         axis = 1)

# Export merged db
m_db.to_csv(args["output_file"], index=False)
