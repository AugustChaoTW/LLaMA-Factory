#!/bin/bash
# Generate Thinking Format Dataset using Model Inference
# This script runs a model in Docker to generate thinking-format training data

set -e

# Start total timer
TOTAL_START_TIME=$(date +%s)

echo "=========================================="
echo "Thinking Data Generation Workflow"
echo "=========================================="
echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Configuration
CONTAINER_NAME="llama-factory-thinking-gen"
CONFIG_FILE="${1:-itri/inference/gpt_lora_120b_sft.yaml}"
INPUT_FILE="${2:-data/npu-csie/deid/account.txt}"
OUTPUT_FILE="${3:-data/npu-csie/deid/account_dataset_thinking_generated.json}"
CLEANUP_CONTAINER="${4:-yes}"  # yes/no - whether to cleanup container after completion
SYSTEM_PROMPT="${5:-你是一個專業的資安日誌去識別化助手。請根據使用者提供的內容，進行去識別化處理並提供對照表。}"

echo "Configuration:"
echo "  Container: $CONTAINER_NAME"
echo "  Model Config: $CONFIG_FILE"
echo "  Input File: $INPUT_FILE"
echo "  Output File: $OUTPUT_FILE"
echo "  Cleanup After: $CLEANUP_CONTAINER"
echo ""

# Resolve input files (support wildcards, directories, and single files)
INPUT_FILES=()

if [[ "$INPUT_FILE" == *"*"* ]]; then
    # Wildcard pattern - expand it
    echo "→ Expanding wildcard pattern: $INPUT_FILE"
    for file in $INPUT_FILE; do
        if [ -f "$file" ]; then
            INPUT_FILES+=("$file")
        fi
    done
elif [ -d "$INPUT_FILE" ]; then
    # Directory - find all .txt files
    echo "→ Scanning directory for .txt files: $INPUT_FILE"
    while IFS= read -r -d '' file; do
        INPUT_FILES+=("$file")
    done < <(find "$INPUT_FILE" -maxdepth 1 -name "*.txt" -type f -print0)
elif [ -f "$INPUT_FILE" ]; then
    # Single file
    INPUT_FILES=("$INPUT_FILE")
else
    echo "❌ Error: Input not found: $INPUT_FILE"
    exit 1
fi

# Check if we found any files
if [ ${#INPUT_FILES[@]} -eq 0 ]; then
    echo "❌ Error: No input files found matching: $INPUT_FILE"
    exit 1
fi

echo "📊 Found ${#INPUT_FILES[@]} file(s) to process:"
for file in "${INPUT_FILES[@]}"; do
    lines=$(wc -l < "$file")
    echo "  - $file ($lines lines)"
done
echo ""

# Check if we're already in a container
IN_CONTAINER=false
if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    IN_CONTAINER=true
    echo "✓ Already running inside container"
else
    echo "→ Running on host, will use container: $CONTAINER_NAME"
fi

echo ""
echo "=========================================="
echo "Step 1: Prepare Docker Container"
echo "=========================================="

CONTAINER_START_TIME=$(date +%s)

if [ "$IN_CONTAINER" = false ]; then
    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$" 2>/dev/null; then
        echo "⚠ Container '$CONTAINER_NAME' already exists"
        
        # Stop and remove old container
        echo "→ Stopping and removing old container..."
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
        echo "✓ Old container removed"
    fi
    
    # Start new container in detached mode with SINGLE GPU
    echo "→ Starting new container with 1 GPU..."
    
    # Get the LLaMA-Factory root directory (go up 2 levels from scripts/itri-npu-csie)
    LLAMA_FACTORY_ROOT="$(cd ../../ && pwd)"
    
    docker run -d \
        --name "$CONTAINER_NAME" \
        --gpus '"device=0"' \
        --ipc=host \
        --ulimit memlock=-1 \
        --ulimit stack=67108864 \
        -v "$LLAMA_FACTORY_ROOT":/workspace/LLaMA-Factory \
        -v ~/.cache/huggingface:/root/.cache/huggingface \
        -w /workspace/LLaMA-Factory \
        nvcr.io/nvidia/pytorch:25.10-py3 \
        tail -f /dev/null
    
    echo "✓ Container started with GPU 0"
    sleep 2
fi

CONTAINER_SETUP_TIME=$(($(date +%s) - CONTAINER_START_TIME))
echo ""
echo "⏱ Container setup time: ${CONTAINER_SETUP_TIME}s"

echo ""
echo "=========================================="
echo "Step 2: Setup and Start API Server"
echo "=========================================="

API_START_TIME=$(date +%s)

if [ "$IN_CONTAINER" = true ]; then
    # We're in container, run directly
    echo "→ Setting up in current container..."
    bash run_inference.sh api "$CONFIG_FILE" &
    API_PID=$!
    echo "API server started (PID: $API_PID)"
else
    # Run in container
    echo "→ Installing dependencies in container (this may take 5-10 minutes)..."
    echo "   Please be patient..."
    
    # Start API server in background and capture output
    docker exec -d "$CONTAINER_NAME" bash -c "cd /workspace/LLaMA-Factory && bash run_inference.sh api $CONFIG_FILE > /tmp/api_setup.log 2>&1"
    
    echo "✓ Installation and API startup initiated"
    echo ""
    echo "→ Monitoring installation progress..."
    
    # Monitor installation with timeout
    INSTALL_TIMEOUT=600  # 10 minutes for installation
    INSTALL_WAITED=0
    
    while [ $INSTALL_WAITED -lt $INSTALL_TIMEOUT ]; do
        # Check if API is ready
        if docker exec "$CONTAINER_NAME" curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
            echo ""
            echo "✓ Installation complete and API is ready!"
            break
        fi
        
        # Show progress every 10 seconds
        if [ $((INSTALL_WAITED % 10)) -eq 0 ]; then
            # Try to get last log line
            LAST_LOG=$(docker exec "$CONTAINER_NAME" tail -1 /tmp/api_setup.log 2>/dev/null || echo "Installing...")
            echo "  [${INSTALL_WAITED}s] $LAST_LOG"
        fi
        
        sleep 2
        INSTALL_WAITED=$((INSTALL_WAITED + 2))
    done
    
    if [ $INSTALL_WAITED -ge $INSTALL_TIMEOUT ]; then
        echo ""
        echo "ERROR: Installation/API startup failed or timed out after ${INSTALL_TIMEOUT} seconds"
        echo ""
        echo "Installation logs:"
        echo "===================="
        docker exec "$CONTAINER_NAME" cat /tmp/api_setup.log 2>/dev/null || echo "No logs available"
        echo "===================="
        
        # Cleanup
        if [ "$CLEANUP_CONTAINER" = "yes" ]; then
            echo "Cleaning up container..."
            docker stop "$CONTAINER_NAME" 2>/dev/null || true
            docker rm "$CONTAINER_NAME" 2>/dev/null || true
        fi
        
        exit 1
    fi
fi

API_SETUP_TIME=$(($(date +%s) - API_START_TIME))
echo "⏱ API setup time: ${API_SETUP_TIME}s"

echo ""
echo "=========================================="
echo "Step 3: Generate Thinking Format Data"
echo "=========================================="

GEN_START_TIME=$(date +%s)

# Calculate total lines across all files
TOTAL_INPUT_LINES=0
for file in "${INPUT_FILES[@]}"; do
    lines=$(wc -l < "$file")
    TOTAL_INPUT_LINES=$((TOTAL_INPUT_LINES + lines))
done

echo "📊 Total input: $TOTAL_INPUT_LINES lines across ${#INPUT_FILES[@]} file(s)"
echo ""

# Create Python script for inference
INFERENCE_SCRIPT="/tmp/generate_thinking_data.py"

if [ "$IN_CONTAINER" = true ]; then
    SCRIPT_PATH="$INFERENCE_SCRIPT"
else
    SCRIPT_PATH="$INFERENCE_SCRIPT"
fi

# Generate the Python inference script
cat > "$INFERENCE_SCRIPT" << 'PYTHON_SCRIPT_EOF'
#!/usr/bin/env python3
"""
Generate thinking format dataset using model inference
"""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict
import requests

def call_api(prompt: str, system_prompt: str, api_url: str = "http://localhost:8000/v1/chat/completions") -> str:
    """Call the API to get model response"""
    payload = {
        "model": "default",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ✗ API call failed: {e}", file=sys.stderr)
        return None

def parse_response(response: str) -> tuple:
    """Parse response to extract thinking and answer"""
    # Try to find <thinking> tags
    if "<thinking>" in response and "</thinking>" in response:
        start = response.find("<thinking>") + len("<thinking>")
        end = response.find("</thinking>")
        thinking = response[start:end].strip()
        answer = response[end + len("</thinking>"):].strip()
    else:
        # No thinking tags, treat entire response as answer
        thinking = ""
        answer = response.strip()
    
    return thinking, answer

def generate_thinking_dataset(
    input_files: List[str],
    output_file: str,
    system_prompt: str,
    instruction_template: str = "以下內容請幫我去識別化並加上對照表：\n\n{content}"
):
    """Generate thinking format dataset from input files"""
    
    # Load all lines from all input files
    all_lines = []
    for input_file in input_files:
        print(f"Loading input from: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [(line.strip(), input_file) for line in f if line.strip()]
            all_lines.extend(lines)
    
    print(f"Processing {len(all_lines)} lines from {len(input_files)} file(s)...")
    print("")
    
    dataset = []
    success_count = 0
    fail_count = 0
    
    for idx, (line, source_file) in enumerate(all_lines, 1):
        print(f"[{idx}/{len(all_lines)}] Processing from {Path(source_file).name}...")
        
        # Create instruction
        instruction = instruction_template.format(content=line)
        
        # Call API
        response = call_api(instruction, system_prompt)
        
        if response:
            # Parse response
            thinking, answer = parse_response(response)
            
            # Create thinking format entry
            entry = {
                "messages": [
                    {
                        "role": "user",
                        "content": instruction
                    }
                ]
            }
            
            # Add thinking if present
            if thinking:
                entry["messages"].append({
                    "role": "assistant_thought",
                    "content": thinking
                })
            
            # Add answer
            entry["messages"].append({
                "role": "assistant",
                "content": answer
            })
            
            dataset.append(entry)
            success_count += 1
            print(f"  ✓ Success ({len(answer)} chars)")
        else:
            fail_count += 1
            print(f"  ✗ Failed")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.1)
    
    # Save dataset
    print("")
    print(f"Saving to: {output_file}")
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print("")
    print("=" * 60)
    print(f"Generation complete!")
    print(f"  Success: {success_count}/{len(all_lines)}")
    print(f"  Failed: {fail_count}/{len(all_lines)}")
    print(f"  Output: {output_file}")
    print(f"  Size: {output_path.stat().st_size / 1024:.2f} KB")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: generate_thinking_data.py <input_files...> <output_file> <system_prompt>")
        sys.exit(1)
    
    # Last two arguments are output_file and system_prompt
    # Everything before that is input files
    output_file = sys.argv[-2]
    system_prompt = sys.argv[-1]
    input_files = sys.argv[1:-2]
    
    if not input_files:
        print("Error: No input files specified")
        sys.exit(1)
    
    generate_thinking_dataset(input_files, output_file, system_prompt)
PYTHON_SCRIPT_EOF

# Run the inference script
if [ "$IN_CONTAINER" = true ]; then
    # Run directly
    python3 "$INFERENCE_SCRIPT" "${INPUT_FILES[@]}" "$OUTPUT_FILE" "$SYSTEM_PROMPT"
    GEN_EXIT_CODE=$?
else
    # Copy script to container and run
    docker cp "$INFERENCE_SCRIPT" "$CONTAINER_NAME:/tmp/generate_thinking_data.py"
    docker exec -it "$CONTAINER_NAME" python3 /tmp/generate_thinking_data.py "${INPUT_FILES[@]}" "$OUTPUT_FILE" "$SYSTEM_PROMPT"
    GEN_EXIT_CODE=$?
fi

GEN_TIME=$(($(date +%s) - GEN_START_TIME))
TOTAL_TIME=$(($(date +%s) - TOTAL_START_TIME))

echo ""
echo "=========================================="
echo "⏱ Timing Report"
echo "=========================================="
echo "Container Setup:    ${CONTAINER_SETUP_TIME}s"
echo "API Setup:          ${API_SETUP_TIME}s"
echo "Data Generation:    ${GEN_TIME}s"
echo "----------------------------------------"
echo "Total Time:         ${TOTAL_TIME}s ($(printf '%02d:%02d' $((TOTAL_TIME/60)) $((TOTAL_TIME%60))))"
echo "=========================================="

# Calculate throughput
if [ $GEN_EXIT_CODE -eq 0 ]; then
    SAMPLES_PER_SEC=$(echo "scale=2; $TOTAL_INPUT_LINES / $GEN_TIME" | bc 2>/dev/null || echo "N/A")
    AVG_TIME_PER_SAMPLE=$(echo "scale=2; $GEN_TIME / $TOTAL_INPUT_LINES" | bc 2>/dev/null || echo "N/A")
    
    echo ""
    echo "📊 Performance Metrics"
    echo "=========================================="
    echo "Samples Processed:  $TOTAL_INPUT_LINES"
    echo "Throughput:         ${SAMPLES_PER_SEC} samples/sec"
    echo "Avg Time/Sample:    ${AVG_TIME_PER_SAMPLE}s"
    echo "=========================================="
fi

echo ""
echo "=========================================="
echo "Workflow Complete!"
echo "=========================================="
echo "End Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

if [ $GEN_EXIT_CODE -eq 0 ]; then
    echo "✅ Data generation completed successfully!"
    echo ""
    echo "Output file: $OUTPUT_FILE"
else
    echo "❌ Data generation failed with exit code: $GEN_EXIT_CODE"
fi

echo ""

# Cleanup container if requested
if [ "$IN_CONTAINER" = false ]; then
    if [ "$CLEANUP_CONTAINER" = "yes" ]; then
        echo "Cleaning up container..."
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
        echo "✓ Container removed"
    else
        echo "Container '$CONTAINER_NAME' is still running."
        echo ""
        echo "To stop it:  docker stop $CONTAINER_NAME"
        echo "To remove it: docker rm $CONTAINER_NAME"
        echo "To enter it: docker exec -it $CONTAINER_NAME bash"
    fi
fi

echo ""

exit $GEN_EXIT_CODE
