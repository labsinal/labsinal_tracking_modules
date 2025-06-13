"""
Module that creates a distribution plot for detected mitosis, ground truth and the validations
"""

######################################
# imports
from pandas import DataFrame, read_csv
import matplotlib.pyplot as plt
import seaborn as sns

######################################
# Define helper functions

def create_graph(mitosis_table : DataFrame, title=""):
    """
    Function that create distribution plots from mitosis tables
    
    params:
    mitosis_table : pandas.DataFrame | Mitosis table
    title : str ("") | Graph's title
    return: Graph
    """
    mitosis_table["t"] = mitosis_table["t"] / 2 / 24
    sns.displot(mitosis_table, x = "t")

def create_filtered_tables(tracking_mitosis:DataFrame, ground_truth:DataFrame) -> tuple[DataFrame]:
    """
    Function that create metrics tables from tracking and ground truth

    params:
    tracking_mitosis : pandas.DataFrame | Detected mitosis table
    ground_truth : pandas.DataFrame | Ground truth mitosis table
    return : tuple | Tuple with filtered dataframes (true positives, false positives, false negatives)
    """
    ...

def create_distributions(tracking_mitosis:DataFrame, ground_truth:DataFrame) -> None:
    """
    Function that create distributions for mitosis detection, false positives, false negatives and true negatives.

    params:
    tracking_mitosis : pandas.DataFrame | Detected mitosis table
    ground_truth : pandas.DataFrame | Ground truth mitosis table
    """
    ...

######################################
# Define main function

def main() -> None:
    """
    Code's main function
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(description="")

    parser.add_argument("-a",
                        action="store",
                        required=True,
                        dest="a",
                        help="Help a")
######################################
# Call main function id runned directly
if __name__ == "__main__":
    main()

# end of current module
