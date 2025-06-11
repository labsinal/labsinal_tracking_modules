"""
Module that evaluates the proportion of right mitosis
    ◍ bash-debug-adapter
    ◍ bash-language-server bashls
"""

####################################
from argparse import ArgumentParser

from pandas import DataFrame
from pandas import read_csv, merge

from ultrack_modules.mitosis_evaluation.isolate_mitosis import isolate_mitosis

####################################
# Define Argument Parsing Function

def get_args_dict() -> dict:
    """
    Function that reads the cli arguments and returns
    a dict containing them.
    :return: dict | Dictionary with cli passed arguments
    """
    
    # defining program description
    description = "DESCRIPTION"
    
    # creating a parser instance
    parser = ArgumentParser(description=description)
    
    # adding arguments to parser
    parser.add_argument("-gt", "--ground_truth",
                        action="store",
                        required=True,
                        dest="ground_truth",
                        help="Table with the manually annotated mitosis as ground truth values (.csv)")

    parser.add_argument("-t", "--tracking_table",
                        action="store",
                        required=True,
                        dest="tracking_table",
                        help="Table from ultrack (.csv)")

    parser.add_argument("--t-tolerance", "-tt",
                        action="store",
                        required=False,
                        default=2,
                        type=int,
                        dest="t_tolerance",
                        help="Tolerance to check mitosis in surrounding frames")

    parser.add_argument("--pos-tolerance", "-pt",
                        action="store",
                        required=False,
                        default=20.0,
                        type=float,
                        dest="pos_tolerance",
                        help="Tolerance to check mitosis in surrounding positions")

    parser.add_argument("--save_scores",
                        action="store",
                        required=False,
                        dest="save_scores",
                        help="To save scores as a .txt add its path here!")

    parser.add_argument("--is_mitosis",
                        action="store_true",
                        required=False,
                        dest="is_mitosis",
                        help="Add this if the file already is the isolated mitosis")


    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

####################################
# Define Helper Functions

def evaluate_mitosis(ground_truth : DataFrame,
                     tracking : DataFrame,
                     t_tolerance : int,
                     p_tolerance : float) -> tuple:
    """
    Function that evaluates precision, recall and F1-score
    from DataFrames containing mitosis.

    :param ground_truth: DataFrame. Manually annotated ground truth mitosis
    :param tracking: DataFrame. Tracking detected mitosis
    :param t_tolerance: int. Tolerance in respect to time
    :param p_tolerance: int | float. Tolerance in respect to position
    :return: tuple| (precision, recall, F1-score)
    """

    # Create true/false positive/negative variables
    tp = fp = fn = 0

    # Populate variables
    # loop
    l_gt = len(ground_truth)
    for id in tracking["track_id"].unique():
        # Get tracking data
        tracking_data   = tracking[tracking["track_id"] == id]

        tracking_t      = tracking_data.t.item()
        tracking_x      = tracking_data.x.item()
        tracking_y      = tracking_data.y.item()

        filtered_dataset = ground_truth[(ground_truth.t >= tracking_t - t_tolerance) &
                                        (ground_truth.t <= tracking_t + t_tolerance) &
                                        (ground_truth.x >= tracking_x - p_tolerance) &
                                        (ground_truth.x <= tracking_x + p_tolerance) &
                                        (ground_truth.y >= tracking_y - p_tolerance) &
                                        (ground_truth.y <= tracking_y + p_tolerance)]

        ground_truth = (merge(ground_truth ,filtered_dataset,indicator=True, how='outer')
                        .query('_merge=="left_only"').drop('_merge', axis=1))

        if len(filtered_dataset) > 0:
            tp += 1

    fp = len(tracking) - tp
    fn = l_gt - tp

    precision = tp / (tp + fp) if (tp + fp) != 0 else 0

    recall = tp / (tp + fn)

    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) != 0 else 0

    return precision, recall, f1

####################################
# Defining main function
def main() -> None:
    """
    Code's main function.
    :return: None
    """

    # Getting cli arguments dict
    args_dict = get_args_dict()

    # Assign arguments to variables
    ground_truth_path   = args_dict["ground_truth"]
    tracking_table_path = args_dict["tracking_table"]
    pos_tolerance       = args_dict["pos_tolerance"]
    t_tolerance         = args_dict["t_tolerance"]
    save_scores         = args_dict["save_scores"]
    is_mitosis          = args_dict["is_mitosis"]

    # Open tables
    ground_truth_table  = read_csv(ground_truth_path)
    mitosis_table      = read_csv(tracking_table_path)

    if not is_mitosis:
        mitosis_table = isolate_mitosis(mitosis_table)
    
    # Run evaluation function
    precision, recall, f1 = evaluate_mitosis(ground_truth= ground_truth_table,
                                                   tracking= mitosis_table,
                                                   p_tolerance= pos_tolerance,
                                                   t_tolerance= t_tolerance)

    # Print results
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
    print(f"F1-Score: {f1}")

    if save_scores:
        with open(save_scores, "aw") as file:
            file.write(f"Precision: {precision}")
            file.write(f"Recall: {recall}")
            file.write(f"F1-Score: {f1}")


####################################
if __name__ == "__main__":
    main()

# End of current module
