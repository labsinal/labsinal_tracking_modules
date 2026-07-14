# imports
import os
import pandas as pd
from tqdm import tqdm
import cv2
import numpy as np
from glob import glob

# Define helper functions


def apply_displacements(
    displacement_table: pd.DataFrame, images_folder: str, output_folder: str
) -> None:
    """
    Function that applies displacements to images in a foder,
    savin them in a output folder

    Args:
        displacement_table (pd.DataFrame): _description_
        images_folder (str): _description_
        output_folder (str): _description_

    Raises:
        FileNotFoundError: _description_
    """

    # Check if folders exist
    if not os.path.exists(images_folder):
        raise FileNotFoundError(f"Input folder {images_folder} does not exist.")
    os.makedirs(output_folder, exist_ok=True)

    images_paths = sorted(glob(os.path.join(images_folder, "*.tif")))

    for img_path, (_, row) in tqdm(
        zip(images_paths, displacement_table.iterrows()),
        total=len(displacement_table),
        desc="Applying translations",
    ):

        dx = row["dx"]
        dy = row["dy"]

        # Load image
        image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        # Apply translation
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        shifted = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))

        # Save result
        filename = os.path.basename(img_path)
        output_path = os.path.join(output_folder, filename)
        cv2.imwrite(output_path, shifted)


# Define main function
def main() -> None:
    """
    Code main function
    """
    from argparse import ArgumentParser

    # creating a parser instance
    parser = ArgumentParser(description="Apply registration displacements to images")

    # adding arguments to parser
    parser.add_argument(
        "-d",
        "--displacement_table",
        dest="displacement_table",
        required=True,
        help="Defines path to the displacement table (.csv)",
    )

    parser.add_argument(
        "-i",
        "--input_folder",
        dest="input_folder",
        required=True,
        help="Defines path to the folder containing images",
    )

    parser.add_argument(
        "-o",
        "--output_folder",
        dest="output_folder",
        required=True,
        help="Defines path to the output folder",
    )

    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # Open displacement table
    displacement_table = pd.read_csv(args_dict["displacement_table"])

    # Call apply_displacements function
    apply_displacements(
        displacement_table=displacement_table,
        images_folder=args_dict["input_folder"],
        output_folder=args_dict["output_folder"],
    )

    print(f"Saved displaced images in {args_dict['output_folder']}.")


# Call main function if runned directly
if __name__ == "__main__":
    main()
