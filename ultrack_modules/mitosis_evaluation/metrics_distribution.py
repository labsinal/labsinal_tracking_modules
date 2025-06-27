"""
Module that creates a distribution plot for detected mitosis, ground truth and the validations
"""

######################################
# imports
from warnings import filterwarnings
from pandas import DataFrame, read_csv, merge, concat
import matplotlib.pyplot as plt
import seaborn as sns

######################################
# Define helper functions

def create_graph(mitosis_table : DataFrame, ax):
    """
    Function that create distribution plots from mitosis tables
    
    params:
    mitosis_table : pandas.DataFrame | Mitosis table
    title : str ("") | Graph's title
    return: Graph
    """
    mitosis_table["t"] = mitosis_table["t"] / 2 / 24
    return sns.displot(ax = ax, x = mitosis_table.t)

def create_metrics_df(tracking_mitosis:DataFrame, 
                      ground_truth:DataFrame,
                      time_tolerance = 3,
                      position_tolerance = 100) -> DataFrame:
    """
    Function that create metrics tables from tracking and ground truth

    params:
    tracking_mitosis : pandas.DataFrame | Detected mitosis table
    ground_truth : pandas.DataFrame | Ground truth mitosis table
    time_tolerance : int (3) | Time tolerance for mitosis validation
    position_tolerance : int (100) | Position tolerance for mitosis validation
    return : pandas.DataFrame | DataFrame with mitosis with their metric collumn
    """
    
    # Create lists to accumulate data
    true_positives_data = []
    false_positives_data = []

    # iterate over each mitosis
    for index, row in tracking_mitosis.iterrows():
        # get the information from the detected mitosis
        tracking_t      = row.t.item()
        tracking_x      = row.x.item()
        tracking_y      = row.y.item()

        # Check the values consideting the tolerances
        filtered_dataset = ground_truth[(ground_truth.t >= tracking_t - time_tolerance) &
                                        (ground_truth.t <= tracking_t + time_tolerance) &
                                        (ground_truth.x >= tracking_x - position_tolerance) &
                                        (ground_truth.x <= tracking_x + position_tolerance) &
                                        (ground_truth.y >= tracking_y - position_tolerance) &
                                        (ground_truth.y <= tracking_y + position_tolerance)]

        # Check if any mitosis was found
        if len(filtered_dataset) > 0:
            # if so, remove line from the truth df
            remove_line = filtered_dataset.iloc[0:1]
            ground_truth = concat([ground_truth, remove_line]).drop_duplicates(keep=False)
            
            # Add line to true positives
            true_positives_data.append(row)
        else:
            # if not add to false positives
            false_positives_data.append(row)

    # Create dataframes
    true_positives = DataFrame(true_positives_data)
    false_positives = DataFrame(false_positives_data)

    true_positives["metric"] = "true-positive"
    false_positives["metric"] = "false-positive"
    ground_truth["metric"] = "false-neagative"

    result = concat([true_positives, false_positives, ground_truth], ignore_index = True) 
    
    return result

def create_distributions(tracking_mitosis:DataFrame, 
                         ground_truth:DataFrame,
                         time_tolerance = 3, 
                         position_tolarance = 100) -> None:
    """
    Function that create distributions for mitosis detection, false positives, false negatives and true negatives.

    params:
    tracking_mitosis : pandas.DataFrame | Detected mitosis table
    ground_truth : pandas.DataFrame | Ground truth mitosis table
    time_tolerance : int (3) | Time tolerance for mitosis validation
    position_tolerance : int (100) | Position tolerance for mitosis validation
    """

    metrics_df = create_metrics_df(tracking_mitosis, ground_truth)

    ground_truth["metric"] = "ground_truth"

    complete_df = concat([metrics_df, ground_truth])

    g = sns.FacetGrid(complete_df, col="metric")
    g.map(sns.histplot, "t", bins=10)
    plt.show()

######################################
# Define main function

def main() -> None:
    """
    Code's main function
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(description="")

    parser.add_argument("-t", "--tracking_table",
                        action="store",
                        required=True,
                        dest="tracking_table",
                        help="Tracking table or mitosis detected my tracking")

    parser.add_argument("-gt", "--ground_truth",
                        action="store",
                        required=True,
                        dest="ground_truth",
                        help="Ground truth mitosis table")

    parser.add_argument("-tt", "--time_tolerance",
                        action="store",
                        required=False,
                        default=3,
                        dest="time_tolerance",
                        help="Time tolerance for mitosis validation")

    parser.add_argument("-pt", "--position_tolerance",
                        action="store",
                        required=False,
                        default=100,
                        dest="position_tolerance",
                        help="Position tolerance for mitosis validation")


    args_dict : dict = vars(parser.parse_args())

    # Open tables
    tracking_df : DataFrame    = read_csv(args_dict["tracking_table"])

    ground_truth_df: DataFrame = read_csv(args_dict["ground_truth"])
    
    create_distributions(tracking_df, ground_truth_df)


######################################
# Call main function id runned directly
if __name__ == "__main__":
    main()

# end of current module
