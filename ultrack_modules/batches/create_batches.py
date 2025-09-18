"""
Python model
"""

######################################
# imports
import os

######################################
# Define helper functions

def create_batches(input_folder: str, output_folder: str, batch_size: int) -> None:
    """
    Create batches of files from input_folder and save them in output_folder.
    
    Args:
        input_folder (str): Path to the folder containing files to be batched.
        output_folder (str): Path to the folder where batches will be saved.
        batch_size (int): Number of files per batch.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    files = [f for f in sorted(os.listdir(input_folder)) if os.path.isfile(os.path.join(input_folder, f))]
    total_files = len(files)
    
    for i in range(0, total_files, batch_size):
        batch_files = files[i:i + batch_size]
        batch_folder = os.path.join(output_folder, f"batch_{i // batch_size + 1}")
        os.makedirs(batch_folder, exist_ok=True)
        
        if i + batch_size < total_files:
            batch_files.append(files[i + batch_size])

        for file in batch_files:
            src = os.path.join(input_folder, file)
            dst = os.path.join(batch_folder, file)
            os.symlink(src, dst)  # Using symlink to avoid copying large files

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
                        dest="input_folder",
                        help="Folder containing files to be batched")
    
    parser.add_argument("-o", "--output",
                        action="store",
                        required=True,
                        dest="output_folder",
                        help="Output folder to save batches")
    
    parser.add_argument("-b", "--batch_size",
                        action="store",
                        required=True,
                        type=int,
                        dest="batch_size",
                        help="Number of files per batch")
    
    args = parser.parse_args()

    create_batches(args.input_folder, args.output_folder, args.batch_size)

    print("Batches created successfully.")


######################################
# Call main function id runned directly
if __name__ == "__main__":
    main()

# end of current module