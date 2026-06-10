"""
Batch segmentation with CellPose-SAM
Tuned for: nuclei with diffuse edges, grayscale, timelapse

Input (auto-detected)
  • FOLDER with individual images (*.tif/.png/...)  → 1 file  = 1 frame
  • STACKED .tif FILE (axis 0 = time, (T,H,W))       → 1 plane = 1 frame
The output matches the input format.

Output (FOLDER mode):
  segmented/
    VID001_t001_mask.tif   ← grayscale mask (pixel = nucleus ID)
    VID001_t002_mask.tif
    ...
  all_rois.zip             ← ALL ROIs from every frame in a single zip
                              named t0001_cell0001, t0002_cell0003, etc.

Output (STACK mode):
  <name>_masks.tif         ← mask stack (T,H,W), uint16, pixel = ID
  <name>_masks_rois.zip    ← all ROIs from every frame

Usage:
    python segment_cellpose.py --input folder/of/images
    python segment_cellpose.py --input video.tif        # single stack

Options:
    --input        Folder with images OR a stacked .tif file (required)
    --output       Output (default: <input>/segmented or <input>_masks.tif)
    --diameter     Diameter in pixels — 0 = auto per image (default: 0)
    --flow         Flow threshold (default: 0.6)
    --cellprob     Cell probability threshold (default: -1.0)
    --min_size     Minimum mask size in pixels (default: 50)
    --tile_norm    Local tile normalization (default: 100, 0=disabled)
    --gpu          Use GPU (default: True)
    --ext          Image extension in folder mode (default: tif)
"""

import argparse
import zipfile
from pathlib import Path

import numpy as np
import tifffile
from natsort import natsorted
from cellpose import models, io
from roifile import ImagejRoi


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",     required=True)
    parser.add_argument("--output",    default=None)
    parser.add_argument("--diameter",  type=float, default=0)
    parser.add_argument("--flow",      type=float, default=0.6)
    parser.add_argument("--cellprob",  type=float, default=-1.0)
    parser.add_argument("--min_size",  type=int,   default=50)
    parser.add_argument("--tile_norm", type=int,   default=100)
    parser.add_argument("--gpu",       action="store_true", default=True)
    parser.add_argument("--ext",       default="tif")
    return parser.parse_args()


def masks_to_rois(masks, frame_index):
    """
    Return a list of (name, bytes) for each ROI in the frame.
    Name:  t{frame:04d}_cell{id:04d}
    Bytes: ImageJ binary .roi format
    """
    rois = []
    for cell_id in range(1, masks.max() + 1):
        ys, xs = np.where(masks == cell_id)
        if len(xs) == 0:
            continue
        roi = ImagejRoi.frompoints(
            np.column_stack([xs, ys]),
            name=f"t{frame_index:04d}_cell{cell_id:04d}"
        )
        rois.append((f"t{frame_index:04d}_cell{cell_id:04d}.roi", roi.tobytes()))
    return rois


def load_frames(input_path, ext):
    """
    Return (frames, names, mode):
      frames : list of 2D arrays (one per frame)
      names  : base name of each frame (no extension), used to name outputs
      mode   : 'folder' or 'stack'
    """
    p = Path(input_path)

    if p.is_file():
        arr = tifffile.imread(str(p))
        if arr.ndim == 2:
            arr = arr[np.newaxis, ...]
        elif arr.ndim != 3:
            raise ValueError(
                f"Expected a 2D/3D stack (T,H,W); got shape {arr.shape}. "
                f"Multichannel stacks (T,C,H,W) are not supported."
            )
        frames = [arr[t] for t in range(arr.shape[0])]
        names = [f"{p.stem}_t{t+1:04d}" for t in range(arr.shape[0])]
        return frames, names, "stack"

    if p.is_dir():
        exts = {f".{ext.lstrip('.')}", ".tif", ".tiff", ".png", ".jpg", ".jpeg"}
        files = natsorted([
            f for f in p.iterdir() if f.suffix.lower() in exts and f.is_file()
        ])
        if not files:
            raise FileNotFoundError(f"No images found in: {p}")
        frames = [io.imread(str(f)) for f in files]
        names = [f.stem for f in files]
        return frames, names, "folder"

    raise FileNotFoundError(f"--input does not exist: {p}")


def main():
    args = parse_args()

    input_path = Path(args.input)

    try:
        frames, names, mode = load_frames(args.input, args.ext)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}")
        return

    if mode == "stack":
        out_tif = (Path(args.output) if args.output
                   else input_path.with_name(f"{input_path.stem}_masks.tif"))
        out_tif.parent.mkdir(parents=True, exist_ok=True)
        zip_path = out_tif.with_name(f"{out_tif.stem}_rois.zip")
        output_label = out_tif
    else:
        output_dir = Path(args.output) if args.output else input_path / "segmented"
        output_dir.mkdir(parents=True, exist_ok=True)
        zip_path = output_dir / "all_rois.zip"
        output_label = output_dir

    print(f"\n{'─'*58}")
    print(f"  CellPose-SAM — Batch Nucleus Segmentation")
    print(f"{'─'*58}")
    print(f"  Input format         : {'single stack' if mode == 'stack' else 'folder of images'}")
    print(f"  Frames found         : {len(frames)}")
    print(f"  Output               : {output_label}")
    print(f"  Diameter             : {'auto per image' if args.diameter == 0 else f'{args.diameter}px'}")
    print(f"  Flow threshold       : {args.flow}")
    print(f"  Cellprob threshold   : {args.cellprob}")
    print(f"  Minimum size         : {args.min_size}px")
    print(f"  Tile normalization   : {'disabled' if args.tile_norm == 0 else f'block {args.tile_norm}px'}")
    print(f"  GPU                  : {args.gpu}")
    print(f"{'─'*58}\n")

    model = models.CellposeModel(gpu=args.gpu, pretrained_model="cpsam")

    normalize_cfg = {"tile_norm_blocksize": args.tile_norm} if args.tile_norm > 0 else True
    diameter = args.diameter if args.diameter > 0 else None

    total_cells = 0
    errors = []
    stack_masks = []   # used only in stack mode

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:

        for frame_idx, (img, name) in enumerate(zip(frames, names), 1):
            print(f"[{frame_idx:03d}/{len(frames)}] {name} ... ", end="", flush=True)
            try:
                masks, flows, styles = model.eval(
                    img,
                    diameter=diameter,
                    normalize=normalize_cfg,
                    flow_threshold=args.flow,
                    cellprob_threshold=args.cellprob,
                    min_size=args.min_size,
                    batch_size=8,
                    resample=False,
                )

                n_cells = int(masks.max())
                total_cells += n_cells
                masks_u16 = masks.astype(np.uint16)

                if mode == "stack":
                    stack_masks.append(masks_u16)
                else:
                    mask_path = output_dir / f"{name}_mask.tif"
                    tifffile.imwrite(str(mask_path), masks_u16)

                for roi_name, roi_bytes in masks_to_rois(masks, frame_idx):
                    zf.writestr(roi_name, roi_bytes)

                print(f"{n_cells} nuclei ✓")

            except Exception as e:
                print(f"ERROR: {e}")
                errors.append((name, str(e)))
                if mode == "stack":
                    # keep the stack time-aligned even if a frame fails
                    stack_masks.append(np.zeros(np.asarray(img).shape[:2], np.uint16))

    if mode == "stack" and stack_masks:
        tifffile.imwrite(str(out_tif), np.stack(stack_masks, axis=0), imagej=True)

    print(f"\n{'─'*58}")
    print(f"  ✅ Done!")
    print(f"  Total nuclei segmented : {total_cells}")
    print(f"  Errors                 : {len(errors)}")
    if errors:
        for name, err in errors:
            print(f"    ✗ {name}: {err}")
    print(f"\n  Files generated:")
    if mode == "stack":
        print(f"    {out_tif.name} → mask stack (T,H,W), pixel = nucleus ID")
        print(f"    {zip_path.name} → all ROIs from every frame")
    else:
        print(f"    segmented/*_mask.tif → one mask per frame (pixel = nucleus ID)")
        print(f"    segmented/all_rois.zip → all ROIs from every frame")
    print(f"                             names: t0001_cell0001, t0001_cell0002, ...")
    print(f"{'─'*58}\n")


if __name__ == "__main__":
    main()
