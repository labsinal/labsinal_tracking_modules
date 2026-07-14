"""
Segmentação em batch com CellPose-SAM
Otimizado para: núcleos com margens difusas, grayscale, timelapse

Entrada (auto-detectada)
  • PASTA com imagens individuais (*.tif/.png/...)  → 1 arquivo = 1 frame
  • ARQUIVO .tif STACKED (eixo 0 = tempo, (T,H,W))   → 1 plano = 1 frame
A saída acompanha o formato da entrada.

Saída (modo PASTA):
  segmented/
    VID001_t001_mask.tif   ← máscara grayscale (pixel = ID do núcleo)
    VID001_t002_mask.tif
    ...
  all_rois.zip             ← TODOS os ROIs de todos os frames num único zip
                              nomeados como t0001_cell0001, t0002_cell0003, etc.

Saída (modo STACK):
  <nome>_masks.tif         ← stack de máscaras (T,H,W), uint16, pixel = ID
  <nome>_masks_rois.zip    ← todos os ROIs de todos os frames

Uso:
    python segment_cellpose.py --input pasta/das/imagens
    python segment_cellpose.py --input video.tif        # stack único

Opções:
    --input        Pasta com imagens OU arquivo .tif stacked (obrigatório)
    --output       Saída (padrão: <input>/segmented ou <input>_masks.tif)
    --diameter     Diâmetro em pixels — 0 = auto por imagem (padrão: 0)
    --flow         Flow threshold (padrão: 0.6)
    --cellprob     Cell probability threshold (padrão: -1.0)
    --min_size     Tamanho mínimo de máscara em pixels (padrão: 50)
    --tile_norm    Normalização local em tiles (padrão: 100, 0=desativado)
    --gpu          Usar GPU (padrão: True)
    --ext          Extensão das imagens no modo pasta (padrão: tif)
"""

import argparse
import zipfile
from pathlib import Path

import numpy as np
import tifffile
from natsort import natsorted
from cellpose import models, io
from roifile import ImagejRoi


# ── argumentos ────────────────────────────────────────────────────────────────

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


# ── converte máscaras em objetos ROI do ImageJ ────────────────────────────────

def masks_to_rois(masks, frame_index):
    """
    Retorna lista de (nome, bytes) para cada ROI no frame.
    Nome: t{frame:04d}_cell{id:04d}
    Bytes: formato .roi binário do ImageJ
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


# ── carrega frames: pasta de imagens OU stack único (auto-detecta) ────────────

def load_frames(input_path, ext):
    """
    Retorna (frames, names, mode):
      frames : lista de arrays 2D (um por frame)
      names  : nome base de cada frame (sem extensão), usado para nomear saídas
      mode   : 'folder' ou 'stack'
    """
    p = Path(input_path)

    # arquivo único → stack
    if p.is_file():
        arr = tifffile.imread(str(p))
        if arr.ndim == 2:
            arr = arr[np.newaxis, ...]
        elif arr.ndim != 3:
            raise ValueError(
                f"Esperava stack 2D/3D (T,H,W); recebi shape {arr.shape}. "
                f"Stacks multicanal (T,C,H,W) não são suportados."
            )
        frames = [arr[t] for t in range(arr.shape[0])]
        names = [f"{p.stem}_t{t+1:04d}" for t in range(arr.shape[0])]
        return frames, names, "stack"

    # pasta → arquivos individuais
    if p.is_dir():
        exts = {f".{ext.lstrip('.')}", ".tif", ".tiff", ".png", ".jpg", ".jpeg"}
        files = natsorted([
            f for f in p.iterdir() if f.suffix.lower() in exts and f.is_file()
        ])
        if not files:
            raise FileNotFoundError(f"Nenhuma imagem encontrada em: {p}")
        frames = [io.imread(str(f)) for f in files]
        names = [f.stem for f in files]
        return frames, names, "folder"

    raise FileNotFoundError(f"--input não existe: {p}")


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    input_path = Path(args.input)

    # carrega frames (pasta ou stack)
    try:
        frames, names, mode = load_frames(args.input, args.ext)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERRO] {e}")
        return

    # define saídas conforme o modo
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
    print(f"  CellPose-SAM — Segmentação de Núcleos em Batch")
    print(f"{'─'*58}")
    print(f"  Formato de entrada   : {'stack único' if mode == 'stack' else 'pasta de imagens'}")
    print(f"  Frames encontrados   : {len(frames)}")
    print(f"  Saída                : {output_label}")
    print(f"  Diâmetro             : {'auto por imagem' if args.diameter == 0 else f'{args.diameter}px'}")
    print(f"  Flow threshold       : {args.flow}")
    print(f"  Cellprob threshold   : {args.cellprob}")
    print(f"  Tamanho mínimo       : {args.min_size}px")
    print(f"  Tile normalization   : {'desativado' if args.tile_norm == 0 else f'bloco {args.tile_norm}px'}")
    print(f"  GPU                  : {args.gpu}")
    print(f"{'─'*58}\n")

    model = models.CellposeModel(gpu=args.gpu, pretrained_model="cpsam")

    normalize_cfg = {"tile_norm_blocksize": args.tile_norm} if args.tile_norm > 0 else True
    diameter = args.diameter if args.diameter > 0 else None

    total_cells = 0
    errors = []
    stack_masks = []   # usado só no modo stack

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

                # ── grava a máscara conforme o modo ───────────────────────────
                if mode == "stack":
                    stack_masks.append(masks_u16)
                else:
                    mask_path = output_dir / f"{name}_mask.tif"
                    tifffile.imwrite(str(mask_path), masks_u16)

                # ── ROIs deste frame → acrescenta no zip global ───────────────
                for roi_name, roi_bytes in masks_to_rois(masks, frame_idx):
                    zf.writestr(roi_name, roi_bytes)

                print(f"{n_cells} núcleos ✓")

            except Exception as e:
                print(f"ERRO: {e}")
                errors.append((name, str(e)))
                if mode == "stack":
                    # mantém o stack alinhado no tempo mesmo se um frame falhar
                    stack_masks.append(np.zeros(np.asarray(img).shape[:2], np.uint16))

    # ── no modo stack, grava o stack de máscaras de uma vez ───────────────────
    if mode == "stack" and stack_masks:
        tifffile.imwrite(str(out_tif), np.stack(stack_masks, axis=0), imagej=True)

    print(f"\n{'─'*58}")
    print(f"  ✅ Concluído!")
    print(f"  Total de núcleos segmentados : {total_cells}")
    print(f"  Erros                        : {len(errors)}")
    if errors:
        for name, err in errors:
            print(f"    ✗ {name}: {err}")
    print(f"\n  Arquivos gerados:")
    if mode == "stack":
        print(f"    {out_tif.name} → stack de máscaras (T,H,W), pixel = ID do núcleo")
        print(f"    {zip_path.name} → todos os ROIs de todos os frames")
    else:
        print(f"    segmented/*_mask.tif → uma máscara por frame (pixel = ID do núcleo)")
        print(f"    segmented/all_rois.zip → todos os ROIs de todos os frames")
    print(f"                             nomes: t0001_cell0001, t0001_cell0002, ...")
    print(f"{'─'*58}\n")


if __name__ == "__main__":
    main()