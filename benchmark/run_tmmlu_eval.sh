#!/bin/bash
# TMMLU Benchmark Evaluation Runner
# This script can run both on host and inside Docker container

set -e

# Detect if running in container
IN_CONTAINER=false
if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    IN_CONTAINER=true
fi

# Configuration
CONFIG_FILE="${1:-itri/inference/gpt_lora_120b_sft.yaml}"
API_PORT="${2:-8000}"
MAX_SAMPLES="${3:-100}"  # Default to 100 samples for quick testing
SKIP_API_START="${4:-auto}"  # auto, yes, no

# Determine API URL based on environment
if [ "$IN_CONTAINER" = true ]; then
    API_URL="http://localhost:${API_PORT}"
    echo "🐳 Running inside Docker container"
else
    API_URL="http://localhost:${API_PORT}"
    echo "💻 Running on host"
fi

echo "=========================================="
echo "TMMLU Benchmark Evaluation"
echo "=========================================="
echo "Environment: $([ "$IN_CONTAINER" = true ] && echo "Docker Container" || echo "Host")"
echo "Config: $CONFIG_FILE"
echo "API Port: $API_PORT"
echo "API URL: $API_URL"
echo "Max Samples: $MAX_SAMPLES"
echo "=========================================="

# Determine Python command
if [ "$IN_CONTAINER" = true ]; then
    # In container, try different Python locations
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    elif [ -f /usr/bin/python3 ]; then
        PYTHON_CMD="/usr/bin/python3"
    else
        echo "ERROR: Python not found in container"
        exit 1
    fi
else
    # On host, use venv
    if [ -f .venv/bin/python3 ]; then
        PYTHON_CMD=".venv/bin/python3"
    else
        echo "ERROR: Virtual environment not found. Please run from LLaMA-Factory root directory."
        exit 1
    fi
fi

echo "Python: $PYTHON_CMD"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE"
    exit 1
fi

# Function to check if API is ready
check_api() {
    curl -s "$API_URL/v1/models" > /dev/null 2>&1
    return $?
}

# Determine if we should start API server
START_API=false
if [ "$SKIP_API_START" = "auto" ]; then
    # Auto-detect: check if API is already running
    if check_api; then
        echo "✓ API server already running at $API_URL"
        START_API=false
    else
        echo "⚠ API server not detected"
        if [ "$IN_CONTAINER" = true ]; then
            echo "⚠ In container mode: assuming API will be started separately"
            START_API=false
        else
            echo "→ Will start API server"
            START_API=true
        fi
    fi
elif [ "$SKIP_API_START" = "yes" ]; then
    START_API=false
    echo "→ Skipping API server start (as requested)"
else
    START_API=true
    echo "→ Will start API server"
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Cleaning up..."
    if [ ! -z "$API_PID" ]; then
        echo "Stopping API server (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
        wait $API_PID 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

# Start API server if needed
if [ "$START_API" = true ]; then
    echo ""
    echo "Starting LLaMA-Factory API server..."
    
    # Determine llamafactory-cli command
    if [ "$IN_CONTAINER" = true ]; then
        if command -v llamafactory-cli &> /dev/null; then
            LLAMAFACTORY_CMD="llamafactory-cli"
        elif [ -f /usr/local/bin/llamafactory-cli ]; then
            LLAMAFACTORY_CMD="/usr/local/bin/llamafactory-cli"
        else
            echo "ERROR: llamafactory-cli not found in container"
            exit 1
        fi
    else
        LLAMAFACTORY_CMD=".venv/bin/llamafactory-cli"
    fi
    
    $LLAMAFACTORY_CMD api "$CONFIG_FILE" > benchmark/api_server.log 2>&1 &
    API_PID=$!
    
    echo "API server started (PID: $API_PID)"
    echo "Waiting for API to be ready..."
    
    # Wait for API to be ready (max 60 seconds)
    MAX_WAIT=60
    WAITED=0
    while ! check_api; do
        if [ $WAITED -ge $MAX_WAIT ]; then
            echo "ERROR: API server failed to start within ${MAX_WAIT} seconds"
            echo "Check logs at: benchmark/api_server.log"
            exit 1
        fi
        sleep 2
        WAITED=$((WAITED + 2))
        echo -n "."
    done
    
    echo ""
    echo "API server is ready! ✓"
else
    echo ""
    echo "Checking API availability..."
    if ! check_api; then
        echo "ERROR: API server is not available at $API_URL"
        echo "Please start the API server first:"
        echo "  llamafactory-cli api $CONFIG_FILE"
        exit 1
    fi
    echo "✓ API server is available"
fi

echo ""

# Run evaluation
echo "Starting TMMLU evaluation..."
echo ""

RESULT_FILE="benchmark/results/tmmlu_results_$(date +%Y%m%d_%H%M%S).json"

# Create results directory if it doesn't exist
mkdir -p benchmark/results

$PYTHON_CMD benchmark/tmmlu_eval.py \
    --api-url "$API_URL" \
    --max-samples "$MAX_SAMPLES" \
    --output-dir benchmark/results \
    --output-file "$(basename $RESULT_FILE)"

EVAL_EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Evaluation completed!"
echo "=========================================="

# Check if evaluation was successful
if [ $EVAL_EXIT_CODE -ne 0 ]; then
    echo "ERROR: Evaluation failed with exit code $EVAL_EXIT_CODE"
    if [ "$START_API" = true ]; then
        echo "Check logs at: benchmark/api_server.log"
    fi
    exit $EVAL_EXIT_CODE
fi

# Report evaluation metrics
if [ -f "$RESULT_FILE" ]; then
    echo ""
    echo "📊 Evaluation Metrics Report"
    echo "=========================================="
    
    # Extract metrics using python
    $PYTHON_CMD << EOF
import json
import sys

try:
    with open("$RESULT_FILE", 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Overall metrics
    accuracy = results.get('overall_accuracy', 0)
    correct = results.get('correct', 0)
    total = results.get('total', 0)
    
    print(f"Overall Accuracy: {accuracy:.2%}")
    print(f"Correct Answers: {correct}/{total}")
    print(f"Total Questions: {total}")
    print("")
    
    # Per-subject metrics
    subject_stats = results.get('subject_stats', {})
    if subject_stats:
        print("Per-Subject Performance:")
        print("-" * 60)
        
        # Sort by accuracy (descending)
        sorted_subjects = sorted(
            subject_stats.items(),
            key=lambda x: x[1].get('accuracy', 0),
            reverse=True
        )
        
        for subject, stats in sorted_subjects:
            subj_acc = stats.get('accuracy', 0)
            subj_correct = stats.get('correct', 0)
            subj_total = stats.get('total', 0)
            print(f"  {subject:40s}: {subj_acc:6.2%} ({subj_correct}/{subj_total})")
    
    print("")
    print("=" * 60)
    
except Exception as e:
    print(f"Error reading results: {e}", file=sys.stderr)
    sys.exit(1)
EOF
    
    echo ""
    echo "Results saved in: $RESULT_FILE"
else
    echo "WARNING: Results file not found: $RESULT_FILE"
fi

if [ "$START_API" = true ]; then
    echo "API logs saved in: benchmark/api_server.log"
fi
echo ""
