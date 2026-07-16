"""
Reapply an existing registration from one channel onto another channel.

When one channel of a timelapse has already been registered (drift-corrected),
the same per-frame translation can be transferred to any other channel acquired
at the same stage position. This script recovers that translation and applies it.

How the shift is recovered
    A registered frame alone does not encode how far it was moved, so the shift is
    measured by phase-correlating the reference channel BEFORE and AFTER
    registration: phaseCorrelate(original, registered) returns the translation that
    was applied. That same translation is then applied to the target channel's raw
    frame, keeping every channel co-registered.

    This means you need three folders of the reference channel and target:
      - the reference channel BEFORE registration (--reference-original)
      - the same reference channel AFTER registration (--reference-registered)
      - the unregistered target channel to align            (--target)
    All three must hold the same number of frames, ordered by filename.

Shortcut
    If the registration was produced by register_timelapse.py, a shifts.csv already
    exists and apply_displacements.py applies it directly, without needing the
    original reference frames.

Bit depth
    Frames are read and written with tifffile so the original dtype is preserved.

Usage
    python apply_registration_from_channel.py \
        --reference-original   path/to/red_original \
        --reference-registered path/to/red_registered \
        --target               path/to/green_original \
        --output               path/to/green_registered

    python apply_registration_from_channel.py --selfcheck
"""

import os
from argparse import ArgumentParser

import cv2
import numpy as np
import tifffile
from tqdm import tqdm

from register_timelapse import apply_shift, list_frames, to_gray_float


def transfer_registration(
    original_frames: list, registered_frames: list, target_frames: list, output_folder: str
) -> None:
    """
    Measure the per-frame shift of the reference channel and apply it to the target.

    Args:
        original_frames: Reference channel frames before registration.
        registered_frames: Same reference channel frames after registration.
        target_frames: Unregistered target channel frames to align.
        output_folder: Destination folder (created if missing); target filenames
            are preserved.
    """
    counts = {
        "reference-original": len(original_frames),
        "reference-registered": len(registered_frames),
        "target": len(target_frames),
    }
    if len(set(counts.values())) != 1:
        raise ValueError(f"Folders have different frame counts: {counts}")

    os.makedirs(output_folder, exist_ok=True)

    for original_path, registered_path, target_path in tqdm(
        zip(original_frames, registered_frames, target_frames),
        total=len(target_frames),
        desc="Transferring registration",
    ):
        original = to_gray_float(tifffile.imread(original_path))
        registered = to_gray_float(tifffile.imread(registered_path))

        # phaseCorrelate(original, registered) returns the shift that was applied
        # during the reference registration; reuse it on the target frame.
        (dx, dy), _ = cv2.phaseCorrelate(original, registered)

        target = tifffile.imread(target_path)
        shifted = apply_shift(target, dx, dy)
        tifffile.imwrite(os.path.join(output_folder, os.path.basename(target_path)), shifted)


def _selfcheck() -> None:
    """
    Validate shift recovery and transfer on a synthetic reference/target pair.

    The reference drifts by known steps and its registered version is the drift
    removed; the target shares the same drift but has different content. After
    transfer, every target frame must match the target's first frame.
    """
    import tempfile

    yy, xx = np.mgrid[0:96, 0:96]

    def blobs(centers):
        image = np.zeros((96, 96), dtype=np.float32)
        for cx, cy in centers:
            image += 200.0 * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / 40.0)
        return image

    reference0 = blobs([(24, 30), (60, 40), (45, 70)])
    target0 = blobs([(35, 20), (70, 65), (20, 55)])

    steps = [(3, 1), (2, -2), (-1, 3)]
    cumulative = np.cumsum(np.array(steps, dtype=np.float64), axis=0)

    reference_original = [reference0]
    target_original = [target0]
    for dx, dy in cumulative:
        reference_original.append(apply_shift(reference0, dx, dy))
        target_original.append(apply_shift(target0, dx, dy))
    reference_registered = [reference0] * len(reference_original)

    with tempfile.TemporaryDirectory() as tmp:
        def dump(stack, name):
            folder = os.path.join(tmp, name)
            os.makedirs(folder)
            paths = []
            for index, frame in enumerate(stack):
                path = os.path.join(folder, f"t{index:03d}.tif")
                tifffile.imwrite(path, frame)
                paths.append(path)
            return paths

        out = os.path.join(tmp, "out")
        transfer_registration(
            dump(reference_original, "ref_orig"),
            dump(reference_registered, "ref_reg"),
            dump(target_original, "target"),
            out,
        )

        registered = [tifffile.imread(os.path.join(out, f)) for f in sorted(os.listdir(out))]
        first = registered[0].astype(np.float64)
        for frame in registered:
            diff = np.abs(frame[20:76, 20:76].astype(np.float64) - first[20:76, 20:76]).mean()
            assert diff < 5.0, f"target not aligned, interior mean abs diff {diff:.2f}"

    print("selfcheck passed")


def main() -> None:
    """Parse arguments and transfer the registration, or run the self-check."""
    parser = ArgumentParser(description="Reapply a channel's registration onto another channel")
    parser.add_argument("--selfcheck", action="store_true", help="Run the built-in correctness test and exit")
    parser.add_argument("--reference-original", dest="reference_original", help="Reference channel before registration")
    parser.add_argument(
        "--reference-registered", dest="reference_registered", help="Same reference channel after registration"
    )
    parser.add_argument("--target", help="Unregistered target channel to align")
    parser.add_argument("-o", "--output", help="Output folder for the registered target channel")
    parser.add_argument("--ext", default="tif", help="Frame file extension without the dot (default: tif)")

    args = parser.parse_args()

    if args.selfcheck:
        _selfcheck()
        return

    required = {
        "reference-original": args.reference_original,
        "reference-registered": args.reference_registered,
        "target": args.target,
        "output": args.output,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        parser.error(f"missing required arguments: {', '.join('--' + name for name in missing)}")

    transfer_registration(
        list_frames(args.reference_original, args.ext),
        list_frames(args.reference_registered, args.ext),
        list_frames(args.target, args.ext),
        args.output,
    )

    print(f"Registered target channel saved under {args.output}")


if __name__ == "__main__":
    main()
