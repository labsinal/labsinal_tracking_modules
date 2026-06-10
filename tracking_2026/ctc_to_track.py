import os
import re
import glob
import warnings
import pandas as pd
import tifffile as tiff
from skimage.measure import regionprops
import argparse


def parse_res_track(ctc_folder):
    """
    Read the res_track.txt (or man_track.txt) file from the CTC format and
    return a dictionary mapping track_id -> parent_id.

    File format (one line per track):
        L  B  E  P
        L = track label/ID
        B = start frame (zero-based)
        E = end frame (zero-based)
        P = parent track ID (0 = no parent)

    Returns parent_id as -1 when P == 0 (no defined parent).
    """
    for filename in ("res_track.txt", "man_track.txt"):
        txt_path = os.path.join(ctc_folder, filename)
        if os.path.isfile(txt_path):
            break
    else:
        raise FileNotFoundError(
            f"No 'res_track.txt' or 'man_track.txt' file found in: {ctc_folder}"
        )

    parent_map = {}  # track_id -> parent_id (-1 if no parent)

    with open(txt_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            label, _begin, _end, parent = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            # In the CTC standard, P=0 means "no parent"
            parent_map[label] = parent if parent != 0 else -1

    return parent_map


def _frame_index_from_name(file_path):
    """
    Extract the frame index from the file name (e.g. 'mask003.tif' -> 3),
    rather than relying on the position in the list. This avoids
    desynchronization when frames are missing or names lack zero-padding.
    """
    basename = os.path.basename(file_path)
    match = re.search(r"(\d+)", basename)
    if match is None:
        raise ValueError(f"Could not extract a frame index from: {basename}")
    return int(match.group(1))


def ctc_to_dataframe(ctc_folder):
    """
    Read the CTC-format mask sequence and extract the (x, y) coordinates of
    each track_id per frame, including the 'parent_id' column read from
    res_track.txt.

    parent_id == -1 indicates the cell has no defined parent.

    NOTE on semantics: in CTC, parentage is per TRACK, not per detection.
    Here parent_id is replicated across every row of the track for
    convenience (tidy table). The actual division happens only at the
    transition between the mother's last frame and the daughter's first
    frame — keep that in mind if feeding lineage metrics.
    """
    parent_map = parse_res_track(ctc_folder)

    mask_files = glob.glob(os.path.join(ctc_folder, "mask*.tif"))
    if not mask_files:
        raise FileNotFoundError(f"No 'mask*.tif' image found in: {ctc_folder}")

    # Sort by the numeric index extracted from the name, not lexicographically
    mask_files.sort(key=_frame_index_from_name)

    data = []

    for file_path in mask_files:
        frame_idx = _frame_index_from_name(file_path)
        mask = tiff.imread(file_path)
        props = regionprops(mask)

        for prop in props:
            track_id = prop.label
            # centroid returns (row, column) = (y, x) in image coordinates
            y, x = prop.centroid

            if track_id not in parent_map:
                # Label present in the mask but absent from res_track.txt:
                # this signals a CTC dataset inconsistency, not a normal case.
                warnings.warn(
                    f"track_id {track_id} (frame {frame_idx}) is not in the "
                    f"tracking file; using parent_id=-1. Check the dataset integrity."
                )

            data.append({
                "frame":      frame_idx,
                "track_id":   track_id,
                "position_x": x,
                "position_y": y,
                "parent_id":  parent_map.get(track_id, -1),
            })

    df = pd.DataFrame(data, columns=["frame", "track_id", "position_x", "position_y", "parent_id"])
    return df


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    args = p.parse_args()
    folder_path = args.folder

    df_tracks = ctc_to_dataframe(folder_path)
    df_tracks.to_csv(f"{folder_path}/tracks_coordinates_table.csv", index=False)

    print(df_tracks.head(10))
    print(f"\nTracks with a defined parent: {(df_tracks['parent_id'] != -1).sum()} rows")
    print(f"Tracks without a parent (parent_id == -1): {(df_tracks['parent_id'] == -1).sum()} rows")
