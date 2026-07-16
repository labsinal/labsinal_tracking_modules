"""
Rigid drift correction (registration) for multi-channel microscopy timelapses.

The three channels of a timelapse (bright field, green fluorescence / cytoplasm
and red fluorescence / nucleus) are acquired at the same stage position, so they
share the exact same frame-to-frame drift. This script therefore estimates a
single translation per timepoint from one reference channel and applies that
identical translation to all three channels, keeping them co-registered.

Registration model
    Pure translation (X/Y), which is what stage drift produces. The per-timepoint
    shift is measured with FFT phase correlation (cv2.phaseCorrelate) between each
    frame and the previous one. The sequential shifts are accumulated into an
    absolute correction relative to the first frame, so gradual drift is handled
    even when cells move or divide over time.

Bit depth
    Images are read and written with tifffile so the original dtype is preserved
    (16-bit fluorescence stays 16-bit). warpAffine keeps the input dtype on output.

Input
    One folder per channel, each containing all frames of the timelapse as
    individual TIFF files. The three folders must hold the same number of frames,
    ordered consistently (natural sort by filename).

Output
    One registered folder per channel, created under --output and named
    "<input_folder_name>_registered", with filenames preserved. A shifts.csv with
    the applied dx/dy per frame is written alongside them.

Usage
    python register_timelapse.py \
        --brightfield path/to/bf \
        --green       path/to/green \
        --red         path/to/red \
        --output      path/to/registered \
        [--reference red] [--ext tif]

    python register_timelapse.py --selfcheck   # run the built-in correctness test
"""

import os
import re
from argparse import ArgumentParser
from glob import glob

import cv2
import numpy as np
import pandas as pd
import tifffile
from tqdm import tqdm


def natural_key(path: str) -> list:
    """
    Sort key that orders embedded numbers by value (t2 before t10).

    Args:
        path: File path to derive the key from.

    Returns:
        List of interleaved strings and integers suitable for sorting.
    """
    return [int(chunk) if chunk.isdigit() else chunk for chunk in re.split(r"(\d+)", path)]


def list_frames(folder: str, ext: str) -> list:
    """
    Return the timelapse frames of a folder as a naturally sorted path list.

    Args:
        folder: Folder containing one TIFF per frame.
        ext: File extension to match, without the dot (e.g. "tif").

    Returns:
        Naturally sorted list of file paths (t1, t2, ..., t10, t11).
    """
    frames = sorted(glob(os.path.join(folder, f"*.{ext}")), key=natural_key)
    if not frames:
        raise FileNotFoundError(f"No *.{ext} frames found in {folder}")
    return frames


def to_gray_float(image: np.ndarray) -> np.ndarray:
    """
    Coerce an image to a single-channel float32 array for phase correlation.

    Phase correlation needs a 2D floating-point intensity image; multi-channel
    frames are collapsed to their channel mean.

    Args:
        image: 2D grayscale or 3D (H, W, C) array.

    Returns:
        2D float32 array.
    """
    if image.ndim == 3:
        image = image.mean(axis=-1)
    return image.astype(np.float32)


def estimate_corrections(reference_frames: list) -> np.ndarray:
    """
    Estimate the translation to apply to each frame to cancel cumulative drift.

    Frame-to-previous shifts are measured with phase correlation and accumulated.
    The value returned per frame is the correction that re-centres that frame onto
    the first frame, i.e. the negative of the accumulated drift. Frames are read
    one at a time so only two images are held in memory.

    Args:
        reference_frames: Naturally sorted frame paths of the reference channel.

    Returns:
        Array of shape (n_frames, 2) with the (dx, dy) correction per frame; the
        first frame is (0, 0).
    """
    previous = to_gray_float(tifffile.imread(reference_frames[0]))

    drift = np.zeros(2, dtype=np.float64)
    corrections = [np.zeros(2, dtype=np.float64)]

    for frame_path in tqdm(reference_frames[1:], desc="Estimating drift"):
        current = to_gray_float(tifffile.imread(frame_path))

        # phaseCorrelate(prev, curr) returns the shift that moves prev onto curr,
        # i.e. how much the content drifted between the two frames.
        (step_x, step_y), _ = cv2.phaseCorrelate(previous, current)

        drift += (step_x, step_y)
        corrections.append(-drift.copy())

        previous = current

    return np.array(corrections)


def apply_shift(image: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """
    Translate an image by (dx, dy) with sub-pixel interpolation, preserving dtype.

    Args:
        image: Source image.
        dx: Horizontal shift in pixels (positive moves content right).
        dy: Vertical shift in pixels (positive moves content down).

    Returns:
        Translated image with the same shape and dtype as the input; exposed
        borders are filled with zeros.
    """
    matrix = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]))


def register_channel(frame_paths: list, corrections: np.ndarray, output_folder: str) -> None:
    """
    Apply the per-frame corrections to one channel and write the registered frames.

    Args:
        frame_paths: Naturally sorted frame paths of the channel.
        corrections: (n_frames, 2) correction array from estimate_corrections.
        output_folder: Destination folder (created if missing); input filenames
            are preserved.
    """
    os.makedirs(output_folder, exist_ok=True)
    channel_name = os.path.basename(os.path.normpath(output_folder))

    for frame_path, (dx, dy) in tqdm(
        zip(frame_paths, corrections),
        total=len(frame_paths),
        desc=f"Registering {channel_name}",
    ):
        image = tifffile.imread(frame_path)
        shifted = apply_shift(image, dx, dy)
        tifffile.imwrite(os.path.join(output_folder, os.path.basename(frame_path)), shifted)


def register_timelapse(channels: dict, reference: str, output: str, ext: str) -> None:
    """
    Register all channels of a timelapse against a single reference channel.

    Args:
        channels: Mapping of channel name -> input folder path.
        reference: Channel name used to estimate the drift.
        output: Base output folder; one "<input>_registered" subfolder is created
            per channel.
        ext: Frame file extension without the dot.
    """
    frames = {name: list_frames(folder, ext) for name, folder in channels.items()}

    counts = {name: len(paths) for name, paths in frames.items()}
    if len(set(counts.values())) != 1:
        raise ValueError(f"Channels have different frame counts: {counts}")

    corrections = estimate_corrections(frames[reference])

    os.makedirs(output, exist_ok=True)
    for name, folder in channels.items():
        input_name = os.path.basename(os.path.normpath(folder))
        register_channel(frames[name], corrections, os.path.join(output, f"{input_name}_registered"))

    shifts = pd.DataFrame(corrections, columns=["dx", "dy"])
    shifts.insert(0, "frame", [os.path.basename(p) for p in frames[reference]])
    shifts.to_csv(os.path.join(output, "shifts.csv"), index=False)


def _selfcheck() -> None:
    """
    Validate the drift estimation and sign convention on a synthetic stack.

    A base image of Gaussian blobs is drifted by known integer steps, then the
    pipeline must recover the negated cumulative drift as its correction.
    """
    yy, xx = np.mgrid[0:96, 0:96]
    base = np.zeros((96, 96), dtype=np.float32)
    for cx, cy in [(24, 30), (60, 40), (45, 70), (75, 75)]:
        base += 200.0 * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / 40.0)

    steps = [(3, 1), (2, -2), (-1, 3)]
    true_cumulative = np.cumsum(np.array(steps, dtype=np.float64), axis=0)

    frames = [base]
    for step_x, step_y in steps:
        frames.append(apply_shift(frames[-1], step_x, step_y))

    # apply_shift stacks are exact for integer steps; write to a scratch stack so
    # estimate_corrections exercises the real tifffile read path.
    import tempfile

    corrections = None
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for index, frame in enumerate(frames):
            path = os.path.join(tmp, f"t{index:03d}.tif")
            tifffile.imwrite(path, frame)
            paths.append(path)
        corrections = estimate_corrections(paths)

    expected = np.vstack([[0.0, 0.0], -true_cumulative])
    assert np.allclose(corrections, expected, atol=0.75), (
        f"drift estimation failed:\nexpected\n{expected}\ngot\n{corrections}"
    )
    print("selfcheck passed")


def main() -> None:
    """Parse arguments and register the timelapse, or run the self-check."""
    parser = ArgumentParser(description="Rigid drift correction for multi-channel microscopy timelapses")
    parser.add_argument("--selfcheck", action="store_true", help="Run the built-in correctness test and exit")
    parser.add_argument("-b", "--brightfield", help="Folder with the bright field frames")
    parser.add_argument("-g", "--green", help="Folder with the green fluorescence (cytoplasm) frames")
    parser.add_argument("-r", "--red", help="Folder with the red fluorescence (nucleus) frames")
    parser.add_argument("-o", "--output", help="Base output folder for the registered channels")
    parser.add_argument(
        "--reference",
        choices=["red", "green", "brightfield"],
        default="red",
        help="Channel used to estimate the drift (default: red / nucleus)",
    )
    parser.add_argument("--ext", default="tif", help="Frame file extension without the dot (default: tif)")

    args = parser.parse_args()

    if args.selfcheck:
        _selfcheck()
        return

    required = {"brightfield": args.brightfield, "green": args.green, "red": args.red, "output": args.output}
    missing = [name for name, value in required.items() if value is None]
    if missing:
        parser.error(f"missing required arguments: {', '.join('--' + name for name in missing)}")

    channels = {"brightfield": args.brightfield, "green": args.green, "red": args.red}
    register_timelapse(channels, args.reference, args.output, args.ext)

    print(f"Registered channels saved under {args.output}")


if __name__ == "__main__":
    main()
