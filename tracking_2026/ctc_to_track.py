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
    Lê o arquivo res_track.txt (ou man_track.txt) do formato CTC e retorna
    um dicionário mapeando track_id -> parent_id.

    Formato do arquivo (uma linha por track):
        L  B  E  P
        L = label/ID da track
        B = frame de início (zero-based)
        E = frame de fim (zero-based)
        P = ID da track mãe (0 = sem mãe)

    Retorna parent_id como -1 quando P == 0 (sem mãe definida).
    """
    for filename in ("res_track.txt", "man_track.txt"):
        txt_path = os.path.join(ctc_folder, filename)
        if os.path.isfile(txt_path):
            break
    else:
        raise FileNotFoundError(
            f"Nenhum arquivo 'res_track.txt' ou 'man_track.txt' encontrado em: {ctc_folder}"
        )

    parent_map = {}  # track_id -> parent_id (-1 se sem mãe)

    with open(txt_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            label, _begin, _end, parent = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            # No padrão CTC, P=0 significa "sem mãe"
            parent_map[label] = parent if parent != 0 else -1

    return parent_map


def _frame_index_from_name(file_path):
    """
    Extrai o índice de frame do nome do arquivo (ex.: 'mask003.tif' -> 3),
    em vez de confiar na posição na lista. Isso evita dessincronização
    quando há frames faltando ou nomes sem zero-padding.
    """
    basename = os.path.basename(file_path)
    match = re.search(r"(\d+)", basename)
    if match is None:
        raise ValueError(f"Não foi possível extrair índice de frame de: {basename}")
    return int(match.group(1))


def ctc_to_dataframe(ctc_folder):
    """
    Lê a sequência de máscaras do formato CTC e extrai
    as coordenadas (x, y) de cada track_id por frame,
    incluindo a coluna 'parent_id' lida do res_track.txt.

    parent_id == -1 indica que a célula não possui mãe definida.

    NOTA sobre semântica: no CTC o parentesco é por TRACK, não por detecção.
    Aqui o parent_id é replicado em todas as linhas da track por conveniência
    (tabela tidy). A divisão real ocorre apenas na transição entre o último
    frame da mãe e o primeiro frame da filha — leve isso em conta se for
    alimentar métricas de linhagem.
    """
    parent_map = parse_res_track(ctc_folder)

    mask_files = glob.glob(os.path.join(ctc_folder, "mask*.tif"))
    if not mask_files:
        raise FileNotFoundError(f"Nenhuma imagem 'mask*.tif' encontrada em: {ctc_folder}")

    # Ordena pelo índice numérico extraído do nome, não lexicograficamente
    mask_files.sort(key=_frame_index_from_name)

    data = []

    for file_path in mask_files:
        frame_idx = _frame_index_from_name(file_path)
        mask = tiff.imread(file_path)
        props = regionprops(mask)

        for prop in props:
            track_id = prop.label
            # centroid retorna (linha, coluna) = (y, x) em coordenadas de imagem
            y, x = prop.centroid

            if track_id not in parent_map:
                # Label presente na máscara mas ausente no res_track.txt:
                # isso indica inconsistência no dataset CTC, não um caso normal.
                warnings.warn(
                    f"track_id {track_id} (frame {frame_idx}) não está no arquivo "
                    f"de tracking; usando parent_id=-1. Verifique a integridade do dataset."
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


# --- Execução ---
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    args = p.parse_args()
    folder_path = args.folder

    df_tracks = ctc_to_dataframe(folder_path)
    df_tracks.to_csv(f"{folder_path}/tabela_coordenadas_tracks.csv", index=False)

    print(df_tracks.head(10))
    print(f"\nTracks com mãe definida: {(df_tracks['parent_id'] != -1).sum()} linhas")
    print(f"Tracks sem mãe (parent_id == -1): {(df_tracks['parent_id'] == -1).sum()} linhas")
