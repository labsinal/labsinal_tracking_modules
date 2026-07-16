"""
Keep only the frames of a folder that also exist (by name) in a reference folder.

When channels of a timelapse are preprocessed independently, some frames may be
dropped from one channel, leaving the channels with different frame counts. This
script subsets a target folder to the frames whose filename is also present in a
reference folder, so both end up with the same set of frames.

Matching is by exact filename (basename). The target folder is not modified; the
kept frames are copied to a sibling folder named "<target>_checked".

Usage
    python filter_frames_by_reference.py \
        --reference path/to/reference \
        --target    path/to/fluorescence

    python filter_frames_by_reference.py --selfcheck
"""

import os
import shutil
from argparse import ArgumentParser


def list_files(folder: str) -> list:
    """Return the names of the regular files directly inside a folder."""
    return [name for name in os.listdir(folder) if os.path.isfile(os.path.join(folder, name))]


def filter_by_reference(reference_folder: str, target_folder: str) -> str:
    """
    Copy the target frames whose filename exists in the reference into a new folder.

    Args:
        reference_folder: Folder whose filenames define which frames to keep.
        target_folder: Folder to subset.

    Returns:
        Path of the created "<target>_checked" output folder.
    """
    reference_names = set(list_files(reference_folder))
    target_names = list_files(target_folder)

    output_folder = os.path.normpath(target_folder) + "_checked"
    os.makedirs(output_folder, exist_ok=True)

    kept = 0
    for name in target_names:
        if name in reference_names:
            shutil.copy2(os.path.join(target_folder, name), os.path.join(output_folder, name))
            kept += 1

    print(f"Reference frames: {len(reference_names)}")
    print(f"Target frames:    {len(target_names)}")
    print(f"Kept (matched):   {kept}  ->  {output_folder}")
    print(f"Dropped:          {len(target_names) - kept}")
    return output_folder


def _selfcheck() -> None:
    """Validate that only names present in the reference are copied over."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        reference = os.path.join(tmp, "ref")
        target = os.path.join(tmp, "target")
        os.makedirs(reference)
        os.makedirs(target)

        for name in ["t001.tif", "t002.tif", "t004.tif"]:
            open(os.path.join(reference, name), "w").close()
        for name in ["t001.tif", "t002.tif", "t003.tif", "t004.tif", "t005.tif"]:
            open(os.path.join(target, name), "w").close()

        output = filter_by_reference(reference, target)
        result = set(os.listdir(output))
        assert result == {"t001.tif", "t002.tif", "t004.tif"}, result

    print("selfcheck passed")


def main() -> None:
    """Parse arguments and filter the target folder, or run the self-check."""
    parser = ArgumentParser(description="Keep only the frames whose name exists in a reference folder")
    parser.add_argument("--selfcheck", action="store_true", help="Run the built-in correctness test and exit")
    parser.add_argument("-r", "--reference", help="Folder whose filenames define which frames to keep")
    parser.add_argument("-t", "--target", help="Folder to subset")

    args = parser.parse_args()

    if args.selfcheck:
        _selfcheck()
        return

    missing = [name for name, value in {"reference": args.reference, "target": args.target}.items() if value is None]
    if missing:
        parser.error(f"missing required arguments: {', '.join('--' + name for name in missing)}")

    filter_by_reference(args.reference, args.target)


if __name__ == "__main__":
    main()
