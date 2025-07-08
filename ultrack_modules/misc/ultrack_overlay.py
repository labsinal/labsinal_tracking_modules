"""
Module that given a ultrack output table add ids numbers over the cell video
"""

###########################
# imports

from multiprocessing import Pool
from pandas import DataFrame, read_csv
from functools import partial
from glob import glob
from os import makedirs
from os.path import join, basename
from PIL import Image
from PIL import ImageDraw, ImageFont

###########################
# define helper functions

def add_overlay_from_group(t, group, input_images, output_folder) -> None:
    """
    Funcion that from a grouped df creates a overlayed image

    params:
    t : time from the group
    group : the group itself
    input_images : list of image paths
    output_folder : path to save the images
    """
    
    image_path = input_images[t]

    # open image
    image = Image.open(image_path)

    image = image.convert("RGB")

    draw = ImageDraw.Draw(image)

    font = ImageFont.load_default(size=20)

    # iterate over all cells in the group
    for _, row in group.iterrows():
        
        # get cell coordinates
        x, y = int(row.x), int(row.y)

        # add number to the cell
        draw.text(xy = (x, y), text = str(row.track_id), fill = (0, 255, 0), font=font)
    
    image.save(join(output_folder, basename(image_path)))


def create_crops_from_folder(input_table:DataFrame, input_images_path:str,
                             output_folder:str) -> None:
    """
    Function that creates crops from folder
    """
    
    # Create ordered list of images
    images = sorted(glob(join(input_images_path,"*.tif")))
    images = list(map(lambda x:join(input_images_path, x), images))

    # Group df by frame
    grouped_df = input_table.groupby("t")

    # Create tasks
    tasks = [(t, group) for t, group in grouped_df]

    # Create crops in parallel
    with Pool() as pool:
        pool.starmap(
            partial(
                add_overlay_from_group,
                input_images = images,
                output_folder = output_folder
            ),
            tasks
        )

###########################
# define main function

def main() -> None:
    """
    Code's main function
    """
    # import argument parsing library
    from argparse import ArgumentParser

    # Create parser
    parser = ArgumentParser(description="Given a ultrack output, dimensions and a output folder, create images with nuclei crops")

    # add arguments
    parser.add_argument("-it", "--input_table",
                        action="store",
                        required=True,
                        dest="input_table",
                        help="Ultrack output table (.csv)")

    parser.add_argument("-im", "--input_images",
                        action="store",
                        required=True,
                        dest="input_folder",
                        help="Images to be cropped")

    parser.add_argument("-o", "--output_folder",
                        action="store",
                        required=True, 
                        dest="output",
                        help="Output folder where crops will be saved")

    parser.add_argument("--phenotype", "-p",
                        required=False,
                        help="Defines which other data will be printed with the cells")

    args_dict = vars(parser.parse_args())

    # Open dataframe
    df = read_csv(args_dict["input_table"])

    # make sure output folder exists
    makedirs(args_dict["output"], exist_ok=True)

    # Call main function
    create_crops_from_folder(input_table=df,
                             input_images_path=args_dict["input_folder"],
                             output_folder=args_dict["output"])

##########################
# run code if runned directly
if __name__ == "__main__": 
    main()

