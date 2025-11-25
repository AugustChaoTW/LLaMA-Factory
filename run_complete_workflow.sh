#!/bin/bash
# Complete Workflow: Docker + API + Benchmark
# This script orchestrates the entire evaluation process with timing reports

set -e

# Start total timer
TOTAL_START_TIME=$(date +%s)

echo "=========================================="
echo "TMMLU Benchmark - Complete Workflow"
echo "=========================================="
echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Configuration
CONTAINER_NAME="llama-factory-benchmark"
CONFIG_FILE="${1:-itri/inference/gpt_lora_120b_sft.yaml}"
MAX_SAMPLES="${2:-100}"
CLEANUP_CONTAINER="${3:-yes}"  # yes/no - whether to cleanup container after completion

echo "Configuration:"
echo "  Container: $CONTAINER_NAME"
echo "  Config: $CONFIG_FILE"
echo "  Max Samples: $MAX_SAMPLES"
echo "  Cleanup After: $CLEANUP_CONTAINER"
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
    
    # Start new container in detached mode
    echo "→ Starting new container..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        --gpus all \
        --ipc=host \
        --ulimit memlock=-1 \
        --ulimit stack=67108864 \
        -v $(pwd):/workspace/LLaMA-Factory \
        -v ~/.cache/huggingface:/root/.cache/huggingface \
        -w /workspace/LLaMA-Factory \
        nvcr.io/nvidia/pytorch:25.10-py3 \
        tail -f /dev/null
    
    echo "✓ Container started"
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
    docker exec -d "$CONTAINER_NAME" bash -c "bash run_inference.sh api $CONFIG_FILE > /tmp/api_setup.log 2>&1"
    
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
            echo "  [$((INSTALL_WAITED))s] $LAST_LOG"
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
echo "Step 3: Run TMMLU Benchmark"
echo "=========================================="

EVAL_START_TIME=$(date +%s)

if [ "$IN_CONTAINER" = true ]; then
    # Run directly
    bash benchmark/run_tmmlu_eval.sh "$CONFIG_FILE" 8000 "$MAX_SAMPLES" yes
    EVAL_EXIT_CODE=$?
else
    # Run in container
    echo "→ Running benchmark in container..."
    docker exec -it "$CONTAINER_NAME" bash benchmark/run_tmmlu_eval.sh "$CONFIG_FILE" 8000 "$MAX_SAMPLES" yes
    EVAL_EXIT_CODE=$?
fi

EVAL_TIME=$(($(date +%s) - EVAL_START_TIME))
TOTAL_TIME=$(($(date +%s) - TOTAL_START_TIME))

echo ""
echo "=========================================="
echo "⏱ Timing Report"
echo "=========================================="
echo "Container Setup:    ${CONTAINER_SETUP_TIME}s"
echo "API Setup:          ${API_SETUP_TIME}s"
echo "Evaluation:         ${EVAL_TIME}s"
echo "----------------------------------------"
echo "Total Time:         ${TOTAL_TIME}s ($(printf '%02d:%02d' $((TOTAL_TIME/60)) $((TOTAL_TIME%60))))"
echo "=========================================="

# Calculate throughput
if [ $EVAL_EXIT_CODE -eq 0 ]; then
    SAMPLES_PER_SEC=$(echo "scale=2; $MAX_SAMPLES / $EVAL_TIME" | bc 2>/dev/null || echo "N/A")
    AVG_TIME_PER_SAMPLE=$(echo "scale=2; $EVAL_TIME / $MAX_SAMPLES" | bc 2>/dev/null || echo "N/A")
    
    echo ""
    echo "📊 Performance Metrics"
    echo "=========================================="
    echo "Samples Evaluated:  $MAX_SAMPLES"
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

if [ $EVAL_EXIT_CODE -eq 0 ]; then
    echo "✅ Evaluation completed successfully!"
    echo ""
    echo "Results are saved in: benchmark/results/"
    
    # Show latest result file
    LATEST_RESULT=$(ls -t benchmark/results/tmmlu_results_*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_RESULT" ]; then
        echo "Latest result: $LATEST_RESULT"
    fi
else
    echo "❌ Evaluation failed with exit code: $EVAL_EXIT_CODE"
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

exit $EVAL_EXIT_CODE
