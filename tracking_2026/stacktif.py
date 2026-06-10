#!/usr/bin/env python3
"""
stacktif.py — Stack 2D TIFFs from a directory into a 3D stack (Z, Y, X).

Natural ordering (img2 < img10), shape/dtype validation, optional
incremental (low-RAM) writing, and automatic BigTIFF support.

Deps: numpy, tifffile  ->  pip install numpy tifffile
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import tifffile as tiff

TIFF_EXT = {".tif", ".tiff", ".TIF", ".TIFF"}
# Theoretical limit of classic TIFF (4 GiB). Above this -> BigTIFF.
_BIGTIFF_THRESHOLD = 4_000_000_000


def natural_key(path: Path) -> list:
    """Natural sort key: split the name into digit/non-digit tokens."""
    return [
        int(tok) if tok.isdigit() else tok.lower()
        for tok in re.split(r"(\d+)", path.name)
    ]


def find_tiffs(folder: Path, recursive: bool) -> list[Path]:
    """Collect TIFF files (natural order). Recursion is optional."""
    it: Iterable[Path] = folder.rglob("*") if recursive else folder.iterdir()
    files = [p for p in it if p.is_file() and p.suffix in TIFF_EXT]
    return sorted(files, key=natural_key)


def _probe(path: Path) -> tuple[tuple[int, ...], np.dtype]:
    """Read shape/dtype without loading pixels (uses the header of the first series)."""
    with tiff.TiffFile(path) as tf:
        series = tf.series[0]
        return tuple(series.shape), series.dtype


def _validate(files: list[Path], strict: bool) -> tuple[tuple[int, ...], np.dtype]:
    """Check shape/dtype consistency across slices."""
    ref_shape, ref_dtype = _probe(files[0])
    if strict:
        for p in files[1:]:
            shp, dt = _probe(p)
            if shp != ref_shape or dt != ref_dtype:
                raise ValueError(
                    f"Inconsistency in '{p.name}': shape={shp} dtype={dt} "
                    f"(expected shape={ref_shape} dtype={ref_dtype}). "
                    f"Use --no-strict to skip the pre-check."
                )
    return ref_shape, ref_dtype


def _imagej_metadata(transpose_xy: bool) -> dict:
    axes = "ZXY" if transpose_xy else "ZYX"
    return {"axes": axes}


def write_in_memory(
    files: list[Path],
    out: Path,
    transpose_xy: bool,
    compression: str | None,
) -> tuple[int, ...]:
    """Load everything into RAM and write at once. Fast; for datasets that fit in memory."""
    planes = []
    for i, p in enumerate(files, 1):
        arr = tiff.imread(p)
        if transpose_xy and arr.ndim == 2:
            arr = arr.T
        planes.append(arr)
        print(f"\r  reading {i}/{len(files)}", end="", file=sys.stderr, flush=True)
    print(file=sys.stderr)

    stack = np.stack(planes, axis=0)
    nbytes = stack.nbytes
    tiff.imwrite(
        out,
        stack,
        bigtiff=nbytes > _BIGTIFF_THRESHOLD,
        compression=compression,
        metadata=_imagej_metadata(transpose_xy),
        imagej=compression is None,  # ImageJ can't read arbitrary compression
    )
    return stack.shape


def write_streaming(
    files: list[Path],
    out: Path,
    transpose_xy: bool,
    compression: str | None,
) -> tuple[int, ...]:
    """Write slice by slice. Low RAM usage; ideal for huge stacks."""
    first = tiff.imread(files[0])
    if transpose_xy and first.ndim == 2:
        first = first.T
    plane_bytes = first.nbytes
    big = plane_bytes * len(files) > _BIGTIFF_THRESHOLD

    with tiff.TiffWriter(out, bigtiff=big, imagej=not big and compression is None) as tw:
        meta = _imagej_metadata(transpose_xy)
        for i, p in enumerate(files, 1):
            arr = first if i == 1 else tiff.imread(p)
            if transpose_xy and arr.ndim == 2 and i != 1:
                arr = arr.T
            tw.write(
                arr,
                contiguous=compression is None,
                compression=compression,
                metadata=meta if i == 1 else None,
            )
            print(f"\r  writing {i}/{len(files)}", end="", file=sys.stderr, flush=True)
    print(file=sys.stderr)
    return (len(files), *first.shape)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Stack 2D TIFFs from a folder into a 3D stack (Z, Y, X) in natural order."
    )
    ap.add_argument("folder", type=Path, help="Folder with .tif/.tiff files")
    ap.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Output file (default: <folder>/<folder>_stack.tif)",
    )
    ap.add_argument("-r", "--recursive", action="store_true", help="Recursive search in subfolders")
    ap.add_argument(
        "--streaming", action="store_true",
        help="Write slice by slice (low RAM) instead of loading everything into memory",
    )
    ap.add_argument(
        "--transpose-xy", action="store_true",
        help="Transpose each slice to yield (Z, X, Y) instead of the default (Z, Y, X)",
    )
    ap.add_argument(
        "--compression", default=None,
        help="tifffile compression (e.g. 'zlib', 'lzw', 'zstd'). Default: none (ImageJ-compatible)",
    )
    ap.add_argument(
        "--no-strict", dest="strict", action="store_false",
        help="Skip shape/dtype validation before stacking",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.folder.is_dir():
        print(f"ERROR: '{args.folder}' is not a directory.", file=sys.stderr)
        return 2

    files = find_tiffs(args.folder, args.recursive)
    if not files:
        print(f"ERROR: no TIFF found in '{args.folder}'.", file=sys.stderr)
        return 1

    out = args.output or args.folder / f"{args.folder.resolve().name}_stack.tif"
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(files)} TIFFs. Natural order:", file=sys.stderr)
    for p in files[:5]:
        print(f"  {p.name}", file=sys.stderr)
    if len(files) > 5:
        print(f"  ... (+{len(files) - 5})", file=sys.stderr)

    shape, dtype = _validate(files, args.strict)
    print(f"Reference slice: shape={shape} dtype={dtype}", file=sys.stderr)

    writer = write_streaming if args.streaming else write_in_memory
    final_shape = writer(files, out, args.transpose_xy, args.compression)

    print(f"OK -> {out}  (shape={final_shape}, dtype={dtype})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
