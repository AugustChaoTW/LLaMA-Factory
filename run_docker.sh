#!/bin/bash
# Docker Container Launcher for LLaMA-Factory
# This script starts a Docker container with proper GPU and volume mounts

set -e

CONTAINER_NAME="${1:-llama-factory-benchmark}"
DETACH="${2:-no}"  # yes for detached mode, no for interactive

echo "=========================================="
echo "LLaMA-Factory Docker Container"
echo "=========================================="
echo "Container Name: $CONTAINER_NAME"
echo "Mode: $([ "$DETACH" = "yes" ] && echo "Detached" || echo "Interactive")"
echo "=========================================="

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "⚠ Container '$CONTAINER_NAME' already exists"
    
    # Check if it's running
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "✓ Container is already running"
        echo ""
        echo "To enter the container:"
        echo "  docker exec -it $CONTAINER_NAME bash"
        exit 0
    else
        echo "→ Starting existing container..."
        docker start "$CONTAINER_NAME"
        if [ "$DETACH" = "no" ]; then
            docker attach "$CONTAINER_NAME"
        fi
        exit 0
    fi
fi

# Create new container
echo "Creating new container..."

if [ "$DETACH" = "yes" ]; then
    # Detached mode - keep container running
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
    
    echo "✓ Container started in detached mode"
    echo ""
    echo "To enter the container:"
    echo "  docker exec -it $CONTAINER_NAME bash"
    echo ""
    echo "To stop the container:"
    echo "  docker stop $CONTAINER_NAME"
else
    # Interactive mode
    docker run -it --rm \
        --name "$CONTAINER_NAME" \
        --gpus all \
        --ipc=host \
        --ulimit memlock=-1 \
        --ulimit stack=67108864 \
        -v $(pwd):/workspace/LLaMA-Factory \
        -v ~/.cache/huggingface:/root/.cache/huggingface \
        -w /workspace/LLaMA-Factory \
        nvcr.io/nvidia/pytorch:25.10-py3 \
        bash
fi
