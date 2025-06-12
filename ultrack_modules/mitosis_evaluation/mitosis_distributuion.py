"""
Module that creates a distribution plot for detected mitosis, ground truth and the validations
"""

#############################################
# imports
from pandas import DataFrame, read_csv
import seaborn as sns
import matplotlib.pyplot as plt

#############################################
# Define helper functions

def mitosis_distribution(mitosis:DataFrame):
    """
    Function that calculates mitosis distribution and plots a graph
    """
    mitosis["t"] = mitosis["t"] / 2 / 24
    sns.displot(mitosis, x="t", bins=20)
    plt.show()

#############################################
# Define main function
def main() -> None:
    """
    Code's main function
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Module that 'create distribution of detected mitosis")

    parser.add_argument("-i", "--input",
                        action="store",
                        dest="input",
                        required=True,
                        help="Input table (.csv)")

    args_dict = vars(parser.parse_args())

    input_df = read_csv(args_dict["input"])

    mitosis_distribution(input_df)


#############################################
# Call main function
if __name__ == "__main__": 
    main()

# End of current module
