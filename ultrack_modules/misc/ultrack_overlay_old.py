"""
Code that adds tracking overlays from ultrack csv output
"""

print("Initializing...")

##########################################
# Imports

from numpy import ndarray
from pandas import read_csv
from pandas import DataFrame, Series
from argparse import ArgumentParser
from cv2 import imread, imwrite
from cv2 import cvtColor
from cv2 import putText
from cv2 import COLOR_GRAY2BGR
from cv2 import FONT_HERSHEY_SIMPLEX
from cv2 import line
from os import listdir
from os.path import join

print("All required libraries successfully imported")

##########################################

def get_args_dict() -> dict:
    """
    Parses the cl arguments into a dict
    :return: dict. Represent parsed arguments
    """
    
    # define program description
    description = "add tracking overlays module"
    
    # Creating ArgumentParser instance
    parser = ArgumentParser(description=description)
    
    # Adding arguments
    
    # Input images folder
    parser.add_argument("-i", "--images-folder",
                        dest="images_folder",
                        required=True,
                        help="Defines path to images folder (containing tracked images)")
    
    # Ultrack output file
    parser.add_argument("-t", "--tracking-file",
                        dest="tracking_file",
                        required=True,
                        help="defines path to output file (from tracks_df.to_csv())")
    
    # Output folder
    parser.add_argument("-o", "--output_folder",
                        dest="output_folder",
                        required=True,
                        help="defines path to output folder")
    
    # Argument for if the index will be printed
    parser.add_argument("--print_index",
                        required=False,
                        action="store_true",
                        help="Defines that the cell id will be printed")
    
    # Which collumn will be plotter with the cells
    parser.add_argument("--phenotype", "-p",
                        required=False,
                        help="Defines which other data will be printed with the cells")
    
    # Create args dictionary
    args_dict = vars(parser.parse_args())
    
    return args_dict

##########################################
#Define helper functions

def save_image(open_image:ndarray,
               output_folder:str,
               image_name:str):
    """
    Function that saves the images with overlays
    :param open_image: opened image by cv2
    :param output_folder: path to where the image will br saved
    :param image_name: name of the original image file
    :return: None
    """
    save_name = image_name.replace(".tif", "_overlay.tif")
    save_path = join(output_folder,
                     save_name)
    imwrite(filename=save_path,
            img=open_image)

def add_overlay_to_first_frame(open_image:ndarray,
                               first_frame_df:DataFrame,
                               output_folder:str,
                               image_name:str,
                               print_index:bool):
    """
    Function to add overlays to the first frame
    :open_image: opened image
    :param first_frame_df: data from ultrack
    :param current_ids: id of the cells in the first frame
    :param output_folder: path where the images will be saved
    :param print_index: boolean that defines if the cell index will be printed
    :return: None
    """
    #Get ids in the first frame
    current_ids = first_frame_df['track_id']
    #Iterate over all ids in the first frame
    for id in current_ids:
        
        if print_index:

            # Get the cell point
            current_point = (first_frame_df[first_frame_df["track_id"] == id]["x"],
                             first_frame_df[first_frame_df["track_id"] == id]["y"])
            add_id_to_cell(open_image=open_image,
                           current_point=current_point,
                           index = id)
        
        save_image(open_image, output_folder, image_name)

def add_phenotype_to_cell(open_image:ndarray,
                          current_point:tuple,
                          phenotype:str,
                          v_displacement = 50,
                          h_displacement = 20):
    """
    Given an open image and a number,
    draws number on current image, on
    given set of coordinates
    :param open_image: ndarray. Represents an open image.
    :param coords: Tuple. Represents a cartesian XY coordinate.
    :param num: Integer. Represents a number.
    :return: None.
    """
    # defining other required params for cv2.putText function
    color = (255, 255, 0)
    font_face = FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    text_coord = (current_point[0]+h_displacement, current_point[1]-v_displacement)
    int_coord = tuple(map(int, text_coord))
    
    # drawing text on image
    putText(img=open_image,
            text=phenotype,
            org=int_coord,
            color=color,
            fontFace=font_face,
            fontScale=font_scale)

def add_id_to_cell(open_image:ndarray,
                   current_point:tuple,
                   index:int,
                   v_displacement = 20,
                   h_displacement = 20):
    """
    Given an open image and a number,
    draws number on current image, on
    given set of coordinates
    :param open_image: ndarray. Represents an open image.
    :param current_point: Tuple. Represents a cartesian XY coordinate.
    :param index: Integer. Represents the cell id.
    :param v_displacement: How above from the cell center will be the cell
    :return: None.
    """
    # defining other required params for cv2.putText function
    color = (0, 255, 255)
    text = str(index)
    font_face = FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    text_coord = (current_point[0]+h_displacement, current_point[1]-v_displacement)
    int_coord = tuple(map(int, text_coord))
    
    # drawing text on image
    putText(img=open_image,
            text=text,
            org=int_coord,
            color=color,
            fontFace=font_face,
            fontScale=font_scale)

def load_bgr_img(image_path: str) -> ndarray:
    """
    Given a path to an image,
    returns image as BGR ndarray.
    """
    # opening current image
    current_image = imread(image_path,
                           -1)

    # checking current image shape (grayscale/RGB)
    image_shape = current_image.shape
    image_len = len(image_shape)

    # checking image type
    if image_len < 3:  # not rgb (grayscale)

        # converting current image to rgb
        current_image = cvtColor(current_image, COLOR_GRAY2BGR)

    # returning image
    return current_image

def draw_line(open_image: ndarray,
              coords_a: tuple,
              coords_b: tuple
              ) -> None:
    """
    Given an open image, and two sets
    of coordinates in the cartesian plane,
    draws line between to given points.
    :param open_image: ndarray. Represents an open image.
    :param coords_a: Tuple. Represents a cartesian XY coordinate.
    :param coords_b: Tuple. Represents a cartesian XY coordinate.
    :return: None.
    """ 
    # defining other required params for cv2.line function
    color = 255
    thickness = 2
    
    # converting values to int
    coords_a = tuple(map(int, coords_a))
    coords_b = tuple(map(int, coords_b))
    
    # drawing line on image
    line(img=open_image,
         pt1=coords_a,
         pt2=coords_b,
         color=color,
         thickness=thickness)

def add_overlay_to_cell(cell_df:DataFrame, 
                        open_image:ndarray,
                        print_index:bool,
                        index:int,
                        phenotype:str,
                        n_frame:int):
    """
    Function that adds overlays to each cell in the frame
    :param cell_df: data frame with all data from the cell
    :param open_image: opened image as array
    :param print_index: boolean if the index will be printed
    :param index: index to be printed
    :param phenotype: string that defines which phenotype will be printed
    :param n_frame: number of the actual frame
    :return: None    
    """
    # Get all points in frame order
    points = list(map(lambda x:(x[-1]["x"], x[-1]["y"]), cell_df.iterrows()))
    
    # Set first point
    prev_point = points[0]
    
    if print_index:
        add_id_to_cell(open_image, points[-1], index)
        
    if phenotype != None:
        current_row = cell_df[cell_df["t"] == n_frame]
        phen = str(current_row.iloc[0][phenotype])
        add_phenotype_to_cell(open_image, points[-1], phen)
    
    # For each point draw the line
    for current_point in points[1:]:
        draw_line(open_image, prev_point, current_point)
        prev_point = current_point

def add_overlay_to_frame(tracking_df:DataFrame,
                         n_frame:int,
                         open_image:ndarray,
                         image_name:str,
                         output_folder:str,
                         print_index:bool,
                         phenotype:str):
    """
    Function that receives a points dict and a path to a image
    and adds lines connecting each cell path
    :param tracking_df: dataframe with data from experiments + ultrack
    :param n_frame: index of the current frame
    :param open_image: current opened image
    :param image_name: name for image to be saved
    :param output_folder: where the new images will be saved
    :param print_index: boolean if the index will be printed
    :param phenotype: which phenotype will be printed with the new images
    :return: None
    """
    current_ids = tracking_df[tracking_df["t"] == n_frame]["track_id"]
    for id in current_ids:
        current_df = tracking_df[tracking_df["t"] <= n_frame]
        cell_df = current_df[current_df["track_id"] == id]
        add_overlay_to_cell(cell_df=cell_df,
                            open_image=open_image, 
                            print_index=print_index,
                            index=id,
                            phenotype=phenotype,
                            n_frame = n_frame)
    
        save_image(open_image, output_folder, image_name)
                   
def add_trackings_overlays(images_folder:str, 
                          tracking_file:str,
                          output_folder:str,
                          print_index:bool,
                          phenotype:str
                          ) -> None:
    """
    Function that adds the overlays over an frame
    :param images_folder: path to the folder with the images
    :param tracking file: csv with the tracking data
    :param output_folder: folder where the new images will be saved
    :param print_index: boolean if the index will be printed
    :phenotype: which phenotype will be printed with the new images
    :return: None
    """
    
    # Get input images
    images = sorted(listdir(images_folder))
    
    # Read tracking output:
    print("Reading tracking df ...")
    tracking_df = read_csv(tracking_file)

    # Get frames num
    frames_num = int(tracking_df["t"].max())
    
    # Iterating over frames
    for n_frame in range(frames_num+1):
        
        print(f"{n_frame/(frames_num+1)*100}% | {n_frame} of {frames_num+1}")

        #open image
        open_image = load_bgr_img(join(images_folder, images[n_frame]))
        
        # If is the first frame call specific function
        if n_frame == 0:
            #Filter for data about only the first frame
            first_df = tracking_df[tracking_df["t"]==0]
            add_overlay_to_first_frame(open_image=open_image,
                                       first_frame_df=first_df,
                                       output_folder=output_folder,
                                       image_name=images[n_frame],
                                       print_index = print_index)
        else:
            # Print execution message
            f_string = f"Adding overlays to frame #INDEX# of #TOTAL#"
            
            # Draw lines
            add_overlay_to_frame(tracking_df=tracking_df,
                                 n_frame=n_frame,
                                 open_image=open_image,
                                 image_name=images[n_frame],
                                 output_folder=output_folder,
                                 print_index=print_index,
                                 phenotype=phenotype)    
            
##########################################

def main():
    # Runs the main code
    
    # Get args dict
    args = get_args_dict()
    
    # Run code
    add_trackings_overlays(images_folder=args["images_folder"],
                          tracking_file=args["tracking_file"],
                          output_folder=args["output_folder"],
                          print_index=args["print_index"],
                          phenotype=args["phenotype"])
    

#########################################

# Calling main()
if __name__ == "__main__":
    main()

#########################################
# End of current module
