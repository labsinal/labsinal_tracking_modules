# imports
import os
import cv2
import pandas as pd
import numpy as np
from glob import glob
from tqdm import tqdm

# Define helper functions

def get_displacement_from_folder(original_path:str, registered_path:str) -> pd.DataFrame:
    """
    Function that iterate over each file in folder and get the
    displacement from registration

    params:
    original_path:str 
        Path to the original folder
    registered_path:str
        Path to the registered folder 
    """

    # Get ordered files list
    original_files = sorted(glob(os.path.join(original_path, "*.tif")))
    
    registered_files = sorted(glob(os.path.join(registered_path, "*.tif")))

    # Create data structure that will become df
    df_list = []

    # Iterate over each file
    for original, registered in tqdm(zip(original_files, registered_files),
                                         total=len(original_files),
                                         desc="Processing images"):
        
        # load images
        original_image = cv2.imread(original, cv2.IMREAD_GRAYSCALE)
        registered_image = cv2.imread(registered, cv2.IMREAD_GRAYSCALE)
        
        # Check displacement
        displacement, _ = cv2.phaseCorrelate(
            np.float32(original_image), 
            np.float32(registered_image))

        
        # add data do the df list
        df_list.append({"original_image" : original,
                        "registered_image" : registered,
                        "dx" : displacement[0],
                        "dy" : displacement[1]})
    
    # Return complete df   
    return pd.DataFrame(data=df_list)

# Define main function
def main() -> None:
    """
    Main function to execute the script.
    """
    import sys

    if len(sys.argv) != 3 or sys.argv[1] == "-h":
        print("python3 sync_filenames.py [ORIGINAL/FOLDER] [REGISTERED/FOLDER]")
        return

    # Define folders paths
    original_path = sys.argv[1]
    registered_path = sys.argv[2]

    # Get displacements
    displacements_df = get_displacement_from_folder(original_path, registered_path)
    
    # Save displacements
    filename = os.path.join(registered_path, "displacements.csv")
    displacements_df.to_csv(filename, index=False)
    
    print(f"Displacements table saved to {filename}")

# Call main function if runned as a script
if __name__ == "__main__":
    main()