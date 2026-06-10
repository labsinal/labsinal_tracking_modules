import argparse
import pandas as pd
import tifffile
import numpy as np
import os
import shutil
from skimage.measure import find_contours
from roifile import ImagejRoi, ROI_TYPE


def main():
    parser = argparse.ArgumentParser(description="Extract .roi vectors for Fiji and generate CSVs and a ZIP.")

    parser.add_argument("--csv", required=True, help="Path to the CSV with the curated tracks.")
    parser.add_argument("--image", required=True, help="Path to the original TIF file.")
    parser.add_argument("--mask", required=True, help="Path to the masks.")
    parser.add_argument("--output", required=True, help="Output folder where the ZIP and the new CSVs will be saved.")

    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    roi_folder = os.path.join(args.output, "RoiSet_Fiji")
    os.makedirs(roi_folder, exist_ok=True)

    print(f"Reading CSV: {args.csv}")
    df = pd.read_csv(args.csv)

    print("Loading image and mask TIFs into memory...")
    images = tifffile.imread(args.image)
    masks = tifffile.imread(args.mask)

    # Identify columns and correct the X/Y swap from the curation step
    col_t = 'frame' if 'frame' in df.columns else 't'
    col_id = 'trackId' if 'trackId' in df.columns else 'track_id'
    col_x = 'Center_of_the_object_0' if 'Center_of_the_object_0' in df.columns else 'x'
    col_y = 'Center_of_the_object_1' if 'Center_of_the_object_1' in df.columns else 'y'

    print("Extracting polygons (.roi) frame by frame...")
    new_columns = []

    for idx, row in df.iterrows():
        t = int(row[col_t])
        y = int(row[col_y])
        x = int(row[col_x])
        track_id = int(row[col_id])

        mask_id = masks[t, y, x]

        # Fallback to find the cell if the center lands on the border
        if mask_id == 0:
            window = masks[t, max(0, y - 3):min(images.shape[1], y + 4), max(0, x - 3):min(images.shape[2], x + 4)]
            values = window[window != 0]
            if len(values) > 0:
                mask_id = np.bincount(values).argmax()
            else:
                new_columns.append(("", np.nan, np.nan, np.nan, np.nan))
                continue

        cell_mask = (masks[t] == mask_id)

        contours = find_contours(cell_mask, 0.5)
        if not contours:
            new_columns.append(("", np.nan, np.nan, np.nan, np.nan))
            continue

        contour = max(contours, key=len)
        coords = np.column_stack((contour[:, 1], contour[:, 0])).astype(np.int32)

        name_str = f"frame{t:03d}_label{track_id:03d}_0"
        disk_filename = f"{name_str}.roi"
        roi_path = os.path.join(roi_folder, disk_filename)

        roi = ImagejRoi.frompoints(coords)

        roi.roitype = ROI_TYPE.POLYGON
        roi.name = name_str
        roi.position = t + 1
        roi.tofile(roi_path)

        ymin, xmin = coords[:, 1].min(), coords[:, 0].min()
        ymax, xmax = coords[:, 1].max(), coords[:, 0].max()

        new_columns.append((name_str, ymin, xmin, ymax, xmax))

    df[['ROI_filename', 'bbox_ymin', 'bbox_xmin', 'bbox_ymax', 'bbox_xmax']] = new_columns
    complete_csv = os.path.join(args.output, "tracks_with_rois_complete.csv")
    df.to_csv(complete_csv, index=False)
    print(f"\nComplete table saved to: {complete_csv}")

    print("Generating formatted simplified table...")
    df_simple = pd.DataFrame()
    df_simple['FrameID'] = df[col_t]
    df_simple['CellID'] = df[col_id]
    df_simple['ROI_filename'] = df['ROI_filename']

    # Drop empty rows where no ROI was found for a border cell
    df_simple = df_simple.dropna(subset=['ROI_filename'])
    # Keep IDs as integers (avoid 5.0 instead of 5)
    df_simple['FrameID'] = df_simple['FrameID'].astype(int)
    df_simple['CellID'] = df_simple['CellID'].astype(int)

    simple_csv = os.path.join(args.output, "tracks_simplified.csv")
    df_simple.to_csv(simple_csv, index=False)
    print(f"Simplified table saved to: {simple_csv}")

    print("Compressing ROI folder into ROI Manager format...")
    zip_path = os.path.join(args.output, "RoiSet")
    shutil.make_archive(zip_path, 'zip', roi_folder)
    shutil.rmtree(roi_folder)

    print(f"Success! ZIP file generated at: {zip_path}.zip")


if __name__ == "__main__":
    main()
