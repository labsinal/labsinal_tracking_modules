"""
Module that handles human annotation and fits the tracking data to the annotation.
"""

# imports
from pandas import DataFrame, read_csv

#####################################
# Define helper functions


def deal_with_annotation(annotation_df: DataFrame, tracking_df: DataFrame) -> DataFrame:
    """
    Fit the tracking data to the human annotation.
    """
    # make sure df types
    annotation_df["id"] = annotation_df["id"].astype(str)
    annotation_df["frame"] = annotation_df["frame"].astype(int)
    tracking_df["track_id"] = tracking_df["track_id"].astype(str)

    # iterate through the annotation DataFrame
    for index, row in annotation_df.iterrows():
        fate = row["destino"]
        match fate:
            case "certo":
                # If the annotation is correct, keep the tracking data as is
                continue
            case "troca" | "meio":
                # remove rows with wrong id
                id = row["id"]
                tracking_df = tracking_df[tracking_df["track_id"] != id]
            case "mitose":
                frame = row["frame"]
                id = row["id"]
                # change the id of the cell from the frame onwards
                tracking_df.loc[
                    (tracking_df["track_id"] == id) & (tracking_df["frame"] >= frame),
                    "track_id",
                ] = (
                    id + ".1"
                )

                tracking_df.loc[
                    tracking_df["parent_track_id" == id, "parent_track_id"]
                ] = (id + ".1")
            case "morte":
                # remove the cell from the frame onwards
                frame = row["frame"]
                id = row["id"]
                tracking_df = tracking_df[
                    ~((tracking_df["track_id"] == id) & (tracking_df["frame"] > frame))
                ]

    return tracking_df


#####################################
# Define main function
def main() -> None:
    """
    Code main function
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Deal with human annotation and fit the tracking data to the annotation."
    )

    parser.add_argument(
        "-annotation",
        "-a",
        required=True,
        dest="annotation_file",
        help="Path to the human annotation file (CSV format).",
    )

    parser.add_argument(
        "-tracking",
        "-t",
        required=True,
        dest="tracking_file",
        help="Path to the tracking data file (CSV format).",
    )

    parser.add_argument(
        "-output",
        "-o",
        required=True,
        dest="output_file",
        help="Path to save the fitted tracking data (CSV format).",
    )

    args = parser.parse_args()

    # Load the files
    annotation_df: DataFrame = read_csv(args.annotation_file)
    tracking_df: DataFrame = read_csv(args.tracking_file)

    # Deal with annotation
    fitted_tracking_df: DataFrame = deal_with_annotation(annotation_df, tracking_df)

    # Save the fitted tracking data
    fitted_tracking_df.to_csv(args.output_file, index=False)


#####################################
# Run main function
if __name__ == "__main__":
    main()
