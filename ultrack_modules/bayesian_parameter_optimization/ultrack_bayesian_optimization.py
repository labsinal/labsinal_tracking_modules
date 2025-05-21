"""
Module that uses Bayesian Optimization to maximise ultrack performance
"""
#######################################
# imports

from argparse import ArgumentParser
from bayes_opt import BayesianOptimization
from bayes_opt import acquisition
from dask.array.image import imread
from pandas import read_csv
from pandas import DataFrame
from ultrack.config.config import MainConfig, load_config

from ultrack_modules.tracking.stardist_based.ultrack_track_segmentation import track_segmentation
from ultrack_modules.mitosis_evaluation.mitosis_evaluator import evaluate_mitosis
from ultrack_modules.mitosis_evaluation.isolate_mitosis import isolate_mitosis

#######################################
# Define globals
global SEGMENTATION
global GROUND_TRUTH
global CONFIG

#######################################
# define argument parsing function

def get_args_dict() -> dict:
    """
    Function that reads the cli arguments and returns
    a dict containing them.
    :return: dict | Dictionary with cli passed arguments
    """

    # defining program description
    description = "Module that uses Bayesian Optimization to maximise ultrack performance"

    # creating a parser instance
    parser = ArgumentParser(description=description)

    # adding arguments to parser
    parser.add_argument("-s", "--segmentation",
                        action="store",
                        required=True,
                        dest="segmentation_path",
                        help="Folder containing cell video segmentation")

    parser.add_argument("-gt", "--ground_truth",
                        action="store",
                        required=True,
                        dest="ground_truth_path",
                        help="File containing mitosis ground truth (.csv)")

    parser.add_argument("-c", "--config",
                        action="store",
                        required=True,
                        dest="config_path",
                        help="File containing ultrack settings (.toml)")

    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

#######################################
# define helper functions

def evaluate_ultrack_function(appear_weight:float,
                              disappear_weight:float,
                              division_weight:float) -> float:
    """
    Function that tracks and evaluate the tracking based on a
    appear, disappear and division weights

    :param appear_weight:
    :param disappear_weight:
    :param division_weight:
    :return:
    """
    # open globals
    global SEGMENTATION
    global GROUND_TRUTH
    global CONFIG

    # define weights
    CONFIG.tracking_config.appear_weight = appear_weight
    CONFIG.tracking_config.disappear_weight = disappear_weight
    CONFIG.tracking_config.division_weight = division_weight

    # track video
    tracking_df = track_segmentation(video=SEGMENTATION, config_file=CONFIG)

    # filter tracking mitosis
    mitosis_df = isolate_mitosis(table=tracking_df)

    # evaluate tracking
    precision, recall, f1_score = evaluate_mitosis(ground_truth=GROUND_TRUTH, tracking=mitosis_df,
                                                   t_tolerance=3, p_tolerance=115)

    # return result
    return f1_score

#######################################
# define main function
def main() -> None:
    """
    Code's main function

    :return: None
    """
    # define global variables
    global SEGMENTATION
    global GROUND_TRUTH
    global CONFIG

    # manage cli arguments
    args_dict = get_args_dict()

    SEGMENTATION = imread(args_dict["segmentation_path"] + "/*.tif")
    GROUND_TRUTH = read_csv(args_dict["ground_truth_path"])
    CONFIG = load_config(args_dict["config_path"])

    pbounds = {"appear_weight"      : (-35, 0),
               "disappear_weight"   : (-25, 0),
               "division_weight"    : (-25, 0)}

    acquisition_function = acquisition.UpperConfidenceBound(kappa=0.5)

    optimizer = BayesianOptimization(
        f=evaluate_ultrack_function,
        pbounds=pbounds,
        acquisition_function=acquisition_function,
        verbose=2,
    )

    optimizer.probe(
        params=[-25, -24, -1],
        lazy=True
    )

    optimizer.maximize(
        init_points=2,
        n_iter=14
    )

    print("\n" * 3)
    print(f"Max found: {optimizer.max['target']}")
    print(f"Settings: {optimizer.max['params']}")
    print("\n" * 3)
    print(*optimizer.res, sep="\n")

    df_dict = {"target" : [],
               "appear_weight" : [],
               "disappear_weight" : [],
               "division_weight" : []}

    for dict in optimizer.res:
        df_dict["target"].append(dict["target"])
        df_dict["appear_weight"].append(dict["params"]["appear_weight"])
        df_dict["disappear_weight"].append(dict["params"]["disappear_weight"])
        df_dict["division_weight"].append(dict["params"]["division_weight"])

    df = DataFrame(data=df_dict)
    df.to_csv("data.py")

#######################################
# Call main function
if __name__ == '__main__':
    main()
