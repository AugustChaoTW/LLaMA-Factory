# TMMLU Benchmark Evaluation

This directory contains the evaluation framework for **TMMLU+ (Taiwan Mandarin Massive Language Understanding)** benchmark, integrated with LLaMA-Factory's API.

## Overview

TMMLU+ is a comprehensive benchmark for evaluating Large Language Models on Traditional Chinese (Taiwan Mandarin) understanding. It contains 22,690 multiple-choice questions across 66 subjects, covering educational levels from primary to professional.

## Quick Start

### Option 1: Local API Server

First, start the API server with your model configuration:

```bash
# Start API server in the background
llamafactory-cli api itri/inference/gpt_lora_120b_sft.yaml &
```

Wait a few seconds for the server to start (default port: 8000).

### Option 2: Docker Container API

If your API is running in a Docker container, use the helper script:

```bash
# Get container API information
bash benchmark/docker_api_helper.sh gracious_archimedes

# Run evaluation with container IP
.venv/bin/python3 benchmark/tmmlu_eval.py \
    --api-url http://172.17.0.2:8000 \
    --max-samples 100
```

See [DOCKER_API.md](DOCKER_API.md) for detailed Docker usage instructions.

### 2. Run the Evaluation

```bash
# Quick test with 100 samples
python benchmark/tmmlu_eval.py --max-samples 100

# Full evaluation (all samples)
python benchmark/tmmlu_eval.py

# Evaluate specific subjects
python benchmark/tmmlu_eval.py --subjects "數學" "物理" --max-samples 50

# Custom API URL
python benchmark/tmmlu_eval.py --api-url http://localhost:8000
```

### 3. Using the Helper Script

For convenience, use the provided script:

```bash
# Run quick test (100 samples)
bash benchmark/run_tmmlu_eval.sh

# Or edit the script to customize parameters
```

## Command Line Options

- `--api-url`: LlamaFactory API base URL (default: `http://localhost:8000`)
- `--max-samples`: Maximum number of samples to evaluate (for testing)
- `--subjects`: Specific subjects to evaluate (space-separated)
- `--output-dir`: Output directory for results (default: `benchmark/results`)
- `--output-file`: Output filename for results (default: `tmmlu_results.json`)

## Output

Results are saved in JSON format to `benchmark/results/tmmlu_results.json` and include:

- Overall accuracy
- Per-subject accuracy breakdown
- Detailed results for each question
- Model responses and predictions

## Example Output

```
==============================================================
TMMLU EVALUATION RESULTS
==============================================================
Overall Accuracy: 65.43%
Correct: 654 / 1000

Per-Subject Results:
--------------------------------------------------------------
數學                          : 72.50% (29/40)
物理                          : 68.75% (22/32)
化學                          : 65.00% (26/40)
...
==============================================================
```

## Requirements

- `datasets`: For loading TMMLU+ from HuggingFace
- `requests`: For API communication
- `tqdm`: For progress bars

Install with:
```bash
pip install datasets requests tqdm
```

## Dataset

The evaluation automatically downloads the TMMLU+ dataset from HuggingFace:
- Primary source: `ikala/tmmluplus`
- Alternative: `ZoneTwelve/tmmluplus`

## Architecture

- `tmmlu_eval.py`: Main evaluation script
- `LlamaFactoryAPIClient`: API client for llamafactory-cli
- `TMMLUEvaluator`: Core evaluation logic
- Results are saved in `benchmark/results/`
