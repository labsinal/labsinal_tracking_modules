"""
Module that given a ultrack output table create nuclei crops
in a given dimension.
"""

###########################
# imports

from multiprocessing import Pool
from pandas import DataFrame, read_csv
from functools import partial
from glob import glob
from os import makedirs
from os.path import join
from PIL import Image

###########################
# define helper functions

def crop_from_group(track_id, group, input_images, input_folder,
                    output_folder, width, height, max_frame) -> None:
    
    # make sure folder exists
    id_folder = join(output_folder, str(track_id))
    makedirs(id_folder, exist_ok=True)

    # iterate over each row in the group
    for _, row in group.iterrows():
        # get coordinates
        x, y = int(row.x), int(row.y)
        
        # get t
        t = int(row.t)      

        # open image
        image_path = join(input_folder, input_images[t])
        image = Image.open(image_path)

        # Set cropping coordinates
        left = x - width // 2
        top  = y - height // 2
        right = left + width
        bottom = top + height

        # Create crop
        crop = image.crop((left, top, right, bottom))

        # create output_file
        filename = f"id{track_id}_t{t}_({x},{y}).tif"
        crop.save(join(id_folder, filename))

    last_frame = group.t.max()
    last_frame_data = group[group.t == last_frame]

    x, y = int(last_frame_data.x.iloc[0]), int(last_frame_data.y.iloc[0])

    # Set cropping coordinates
    left = x - width // 2
    top  = y - height // 2
    right = left + width
    bottom = top + height
        
    for i in range(1, min(5, max_frame - last_frame) + 1):
        # open image
        image_path = join(input_folder, input_images[last_frame + i])
        image = Image.open(image_path)

        # Create crop
        crop = image.crop((left, top, right, bottom))

        # create output_file
        filename = f"id{track_id}_t{last_frame + i}_({x},{y}).tif"
        crop.save(join(id_folder, filename))

def create_crops_from_folder(input_table:DataFrame, input_images_path:str,
                             output_folder:str, width = 100, height = 100) -> None:
    """
    Function that creates crops from folder
    """
    
    # Create ordered list of images
    images = sorted(glob(join(input_images_path,"*.tif")))

    # Group df by frame
    grouped_df = input_table.groupby("track_id")

    # Create tasks
    tasks = [(track_id, group) for track_id, group in grouped_df]

    max_frame = int(input_table.t.max())

    # Create crops in parallel
    with Pool() as pool:
        pool.starmap(
            partial(
                crop_from_group,
                input_images = images,
                input_folder = input_images_path,
                output_folder = output_folder,
                width = int(width),
                height = int(height),
                max_frame = max_frame
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

    parser.add_argument("-x", "--width",
                        action="store",
                        required=False,
                        default=100,
                        dest="width",
                        help="Width for the crop (default = 100)")

    parser.add_argument("-y", "--height",
                        action="store",
                        required=False,
                        default=100,
                        dest="height",
                        help="Height for the crop (default = 100)")

    args_dict = vars(parser.parse_args())

    # Open dataframe
    df = read_csv(args_dict["input_table"])

    # Call main function
    create_crops_from_folder(input_table=df,
                             input_images_path=args_dict["input_folder"],
                             output_folder=args_dict["output"],
                             width=args_dict["width"],
                             height=args_dict["height"])

##########################
# run code if runned directly
if __name__ == "__main__": 
    main()
