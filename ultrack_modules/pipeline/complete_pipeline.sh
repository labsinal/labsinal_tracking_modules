#!/bin/bash

# Usage: ./complete_pipeline.sh <input_path> <output_path> <ultrack_config_path>

set -e

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <input_path> <output_path> <ultrack_config_path>"
    exit 1
fi

INPUT_PATH="$1"
ULTRACK_CONFIG="$2"

# Set your conda environment name here
CONDA_ENV_NAME="/home/frederico/envs/tracking-ultrack"

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

# Run preprocess step
echo "Running preprocess..."
PREPROCESSED_DIR="$(dirname "$INPUT_PATH")/preprocessed"
mkdir -p "$PREPROCESSED_DIR"
python ultrack_modules/pipeline/preprocess.py --input "$INPUT_PATH" --output "$PREPROCESSED_DIR"

# Run segmentation step
echo "Running segmentation..."
SEGMENTED_DIR="$(dirname "$INPUT_PATH")/segmented"
mkdir -p "$SEGMENTED_DIR"
python ultrack_modules/pipeline/cellpose_segmentation.py --input "$PREPROCESSED_DIR" --output "$SEGMENTED_DIR"

# Run tracking step
echo "Running tracking..."
TRACKING_DIR="$(dirname "$INPUT_PATH")/trackings"
mkdir -p "$TRACKING_DIR"
python ultrack_modules/pipeline/ultrack_track_segmentation.py --input "$SEGMENTED_DIR" --output "$TRACKING_DIR" --config "$ULTRACK_CONFIG"

echo "Pipeline completed successfully."
