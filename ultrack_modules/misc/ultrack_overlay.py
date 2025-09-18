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

def add_overlay_from_group(t, group, input_images, output_folder, phenotype="", add_frame=False) -> None:
    """
    Function that from a grouped df creates an overlayed image
    """
    image_path = input_images[t]

    # open image
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    # font (default PIL font, since load_default() does not take size param)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()

    if add_frame:
        draw.text(xy=(10, 10), text=f"Frame: {t}", fill=(255, 0, 0), font=font)

    # if there are cells, draw them
    if group is not None and not group.empty:
        for _, row in group.iterrows():
            x, y = int(row.x), int(row.y)

            if phenotype:
                draw.text(xy=(x, y - 20), text=f"{row[phenotype]}", fill=(255, 0, 0), font=font)

            draw.text(xy=(x, y), text=str(row.track_id), fill=(0, 255, 0), font=font)

    image.save(join(output_folder, basename(image_path)))


def create_crops_from_folder(input_table: DataFrame, input_images_path: str,
                             output_folder: str, add_frame: bool,
                             phenotype: str) -> None:
    """
    Function that creates crops from folder
    """

    # Create ordered list of images
    images = sorted(glob(join(input_images_path, "*.tif")))

    # index dataframe by t for fast lookup
    grouped_df = dict(tuple(input_table.groupby("t")))

    # Create tasks for every frame in folder
    tasks = []
    for t, image_path in enumerate(images):
        group = grouped_df.get(t, None)  # None if no detections
        tasks.append((t, group))

    # Run in parallel
    with Pool() as pool:
        pool.starmap(
            partial(
                add_overlay_from_group,
                input_images=images,
                output_folder=output_folder,
                phenotype=phenotype,
                add_frame=add_frame
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
    
    parser.add_argument("--add_frame", "-ap",
                        required=False,
                        action="store_true",
                        help="If set, adds the frame number to the image name")

    args_dict = vars(parser.parse_args())

    # Open dataframe
    df = read_csv(args_dict["input_table"])

    # make sure output folder exists
    makedirs(args_dict["output"], exist_ok=True)

    # Call main function
    create_crops_from_folder(input_table=df,
                             input_images_path=args_dict["input_folder"],
                             output_folder=args_dict["output"],
                             add_frame = args_dict["add_frame"],
                             phenotype = args_dict["phenotype"])

##########################
# run code if runned directly
if __name__ == "__main__": 
    main()

