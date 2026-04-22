# Labsinal Tracking Modules

A collection of Python scripts for cell tracking and analysis in biological research, supporting multiple tracking libraries and providing interoperability with other analysis tools.

## Features

This repository provides tools for:

- **Cell Tracking**: Using Ultrack and Btrack libraries for automated cell lineage tracking
- **Data Conversion**: Seamless integration with other analysis pipelines
  - Convert Ultrack outputs to Clovars format for further analysis
  - Merge Ultrack data with Braind outputs for comprehensive studies
- **Pipeline Automation**: End-to-end processing from raw images to tracked lineages
- **Parameter Optimization**: Bayesian optimization for tracking parameters
- **Validation**: Mitosis detection and tracking quality assessment

## Key Tools

### Data Interoperability

**ultrack_to_clovars.py**: Converts Ultrack tracking results to Clovars-compatible format, enabling integration with Clovars analysis workflows for advanced cell behavior studies.

**merge_ultrack_braind.py**: Combines Ultrack tracking data with Braind segmentation outputs, allowing researchers to leverage both tracking and morphological analysis in a unified dataset.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd labsinal_tracking_modules
   ```

2. Set up the conda environment:
   ```bash
   conda env create -f environments/env_cpu.yml
   conda activate tracking-ultrack  # or your environment name
   ```

3. Install additional dependencies as needed for your specific use case.

## Usage

### Running the Pipeline

Use the provided GUI for an intuitive interface:

```bash
python ultrack_gui.py
```

Or run the pipeline directly:

```bash
./scripts/complete_pipeline.sh <input_path> <output_base_path> <config_path> <conda_env>
```

### Data Conversion

Convert Ultrack to Clovars:
```bash
python ultrack_modules/misc/ultrack_to_clovars.py -i ultrack_output.csv -o clovars_input.csv
```

Merge with Braind data:
```bash
python ultrack_modules/misc/merge_ultrack_braind.py -u ultrack.csv -b braind.csv -o merged.csv
```

## Project Structure

- `ultrack_modules/`: Ultrack-based tracking tools
  - `pipeline/`: Core processing pipeline (preprocessing, segmentation, tracking)
  - `tracking/`: Various tracking implementations
  - `mitosis_evaluation/`: Validation and quality assessment
  - `bayesian_parameter_optimization/`: Parameter tuning
  - `misc/`: Utility scripts including data converters
  - `batches/`: Batch processing tools

- `btrack_modules/`: Btrack-based tracking tools

- `scripts/`: Executable scripts for pipeline automation

- `environments/`: Conda environment configurations

## Contributing

Please ensure all scripts include proper argument parsing and documentation. Follow the existing code style and add tests for new functionality.

## License

[Add your license here]
