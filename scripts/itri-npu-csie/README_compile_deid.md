# DEID Dataset Compiler - Enhanced with API Support

## run api server

`docker exec deid-infer bash -lc "bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml`

## Overview

The `compile_deid_dataset.py` script has been enhanced to support LLM API calls for generating high-quality de-identification responses with thinking sections.

## Features

### ✨ New Features

1. **LLM API Integration**: Call the GPT-OSS-120B API to generate responses
2. **Thinking Sections**: API-generated responses include reasoning process
3. **Parallel Processing**: Concurrent API calls for high throughput (optimized for GB300)
4. **Progress Tracking**: Real-time progress display for each file and example
5. **Retry Logic**: Automatic retry on API failures (3 attempts with 2s delay)
6. **API Connection Test**: Validates API availability before processing
7. **Fallback Mode**: Automatically falls back to placeholder responses if API fails
8. **Command-Line Arguments**: Flexible configuration via CLI

### 📊 Modes

#### **Placeholder Mode** (Default - Fast)
- Generates simple placeholder responses
- No API calls required
- Fast processing (~instant)
- Good for testing structure

#### **API Mode** (High Quality - Slow)
- Calls LLM API for each example
- Generates contextual de-identification responses
- Includes thinking/reasoning sections
- **Parallel Processing**: Uses multiple workers (default: 32) to speed up generation
- Produces higher quality training data

## Usage

### Basic Usage (Placeholder Mode)

```bash
python3 scripts/itri-npu-csie/compile_deid_dataset.py
```

**Output**: `all_dataset_YYYYMMDD_HHMMSS.json`

### API Mode (Recommended for Production)

```bash
python3 scripts/itri-npu-csie/compile_deid_dataset.py --use-api
```

**Output**: `all_dataset_YYYYMMDD_HHMMSS_api.json`

### Custom Configuration

```bash
# Custom API URL and Worker Count
python3 scripts/itri-npu-csie/compile_deid_dataset.py \
  --use-api \
  --api-url http://localhost:8000/v1/chat/completions \
  --max-workers 64

# Custom input directory
python3 scripts/itri-npu-csie/compile_deid_dataset.py \
  --use-api \
  --input-dir /path/to/txt/files

# Custom output filename
python3 scripts/itri-npu-csie/compile_deid_dataset.py \
  --use-api \
  --output-name my_custom_dataset.json
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--use-api` | Enable LLM API mode | `False` (placeholder mode) |
| `--api-url URL` | API endpoint URL | `http://localhost:8000/v1/chat/completions` |
| `--max-workers N` | Number of parallel workers | `32` (optimized for GB300) |
| `--input-dir DIR` | Input directory with .txt files | `/home/fychao/work/LLaMA-Factory/data/npu-csie/deid` |
| `--output-name NAME` | Output filename | `all_dataset_TIMESTAMP[_api].json` |
| `-h, --help` | Show help message | - |

## API Configuration

The script uses these API settings (can be modified in the script):

```python
API_URL = "http://localhost:8000/v1/chat/completions"
API_MODEL = "gpt-oss-120b"
API_TEMPERATURE = 0.6
API_MAX_TOKENS = 2048
API_TIMEOUT = 60  # seconds
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 2  # seconds
MAX_WORKERS = 32  # Default parallel workers
```


## Output Format

### Placeholder Mode Output
```json
{
  "messages": [
    {
      "role": "user",
      "content": "以下內容請幫我去識別化並加上對照表:\n\n帳號 alice 在非上班時間登入..."
    },
    {
      "role": "assistant",
      "content": "[此為來自 account.txt 的原始資料，需要進行去識別化處理]\n\n帳號 alice..."
    }
  ]
}
```

### API Mode Output
```json
{
  "messages": [
    {
      "role": "user",
      "content": "以下內容請幫我去識別化並加上對照表:\n\n帳號 alice 在非上班時間登入..."
    },
    {
      "role": "assistant",
      "content": "<thinking>分析文本中的敏感資訊...</thinking>\n\n帳號 帳號1 在非上班時間登入...\n\n【對照表】\n帳號1 -> alice"
    }
  ]
}
```

## Performance

### Placeholder Mode
- **Speed**: ~instant
- **700 examples**: < 1 second
- **Use case**: Testing, structure validation

### API Mode
- **Speed**: ~2-5 seconds per example
- **700 examples**: ~25-60 minutes
- **Use case**: Production training data

## Example Workflow

### 1. Start the Inference Server

```bash
cd /home/fychao/work/LLaMA-Factory
source .venv/bin/activate
llamafactory-cli api itri/inference/gpt_lora_120b_sft.yaml
```

### 2. Run the Compiler with API Mode

```bash
# In another terminal
cd /home/fychao/work/LLaMA-Factory
python3 scripts/itri-npu-csie/compile_deid_dataset.py --use-api
```

### 3. Monitor Progress

The script will show:
- API connection test result
- Progress for each file (e.g., `[1/100] (1.0%) Generating response via API... ✓`)
- Total time and average time per example

### 4. Use the Generated Dataset

The output file can be directly used with LLaMA-Factory for training:

```yaml
# In your training config
dataset: npu-csie/deid/all_dataset_20251127_HHMMSS_api
```

## Troubleshooting

### API Connection Failed
- **Check**: Is the inference server running?
- **Verify**: `curl http://localhost:8000/docs`
- **Solution**: Start the server with `run_inference.sh`

### Slow Processing
- **Normal**: API mode is slow (~2-5s per example)
- **Expected**: 700 examples = 25-60 minutes
- **Alternative**: Use placeholder mode for quick testing

### Timeout Errors
- **Increase timeout**: Edit `API_TIMEOUT` in the script
- **Check server**: Server may be overloaded

## Files

- **Script**: [`scripts/itri-npu-csie/compile_deid_dataset.py`](file:///home/fychao/work/LLaMA-Factory/scripts/itri-npu-csie/compile_deid_dataset.py)
- **Input**: `data/npu-csie/deid/*.txt`
- **Output**: `data/npu-csie/deid/all_dataset_*.json`
