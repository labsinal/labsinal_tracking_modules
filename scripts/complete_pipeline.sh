#!/bin/bash

#!/bin/bash

# Usage: ./complete_pipeline.sh <input_path> <output_base_path> <ultrack_config_path> <conda_env_name>

set -e

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <input_path> <output_base_path> <ultrack_config_path> <conda_env_name>"
    exit 1
fi

INPUT_PATH="$1"
OUTPUT_BASE="$2"
ULTRACK_CONFIG="$3"
CONDA_ENV_NAME="$4"

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

# Run preprocess step
echo "Running preprocess..."
PREPROCESSED_DIR="$OUTPUT_BASE/preprocessed"
mkdir -p "$PREPROCESSED_DIR"
python ../ultrack_modules/pipeline/preprocess.py --input "$INPUT_PATH" --output "$PREPROCESSED_DIR"

# Run segmentation step
echo "Running segmentation..."
SEGMENTED_DIR="$OUTPUT_BASE/segmented"
mkdir -p "$SEGMENTED_DIR"
python ../ultrack_modules/pipeline/cellpose_segmentation.py --input "$PREPROCESSED_DIR" --output "$SEGMENTED_DIR"

# Run tracking step
echo "Running tracking..."
TRACKING_DIR="$OUTPUT_BASE/trackings"
mkdir -p "$TRACKING_DIR"
python ../ultrack_modules/pipeline/ultrack_track_segmentation.py --input "$SEGMENTED_DIR" --output "$TRACKING_DIR" --config "$ULTRACK_CONFIG"

echo "Pipeline completed successfully."
