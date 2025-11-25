#!/bin/bash
# Docker Container Launcher for LLaMA-Factory
# This script starts a Docker container with proper GPU and volume mounts

set -e

# Show help message
show_help() {
    cat << EOF
Usage: bash run_docker.sh [OPTIONS] [CONTAINER_NAME]

Start a Docker container for LLaMA-Factory with GPU support and volume mounts.

OPTIONS:
    -h, --help       Show this help message and exit
    -d, --detach     Run container in detached mode (background)
    -i, --interactive Run container in interactive mode (default)
    -n, --name NAME  Set container name (default: llama-factory-benchmark)

CONTAINER_NAME:
    Name for the Docker container (default: llama-factory-benchmark)

FEATURES:
    - GPU support (--gpus all)
    - Current directory mounted to /workspace/LLaMA-Factory
    - HuggingFace cache mounted from ~/.cache/huggingface
    - Proper IPC and memory limits for multi-GPU training
    - Uses llama-factory-train-img with pre-installed packages

MODES:
    Interactive (default):
        - Opens bash shell in container
        - Container is removed on exit (--rm)
        - Use for development and debugging

    Detached (-d):
        - Container runs in background
        - Keeps running until stopped
        - Access with: docker exec -it CONTAINER_NAME bash

EXAMPLES:
    # Start interactive container (default)
    bash run_docker.sh

    # Start detached container
    bash run_docker.sh --detach

    # Start with custom name
    bash run_docker.sh --name my-training-container

    # Detached with custom name
    bash run_docker.sh -d -n my-container

    # Enter running container
    docker exec -it llama-factory-benchmark bash

    # Stop detached container
    docker stop llama-factory-benchmark

MOUNTED VOLUMES:
    $(pwd) -> /workspace/LLaMA-Factory (read-write)
    ~/.cache/huggingface -> /root/.cache/huggingface (read-write)

REQUIREMENTS:
    - Docker with GPU support (nvidia-docker2)
    - NVIDIA GPU with drivers installed

EOF
}

# Parse arguments
CONTAINER_NAME="llama-factory-benchmark"
DETACH="no"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--detach)
            DETACH="yes"
            shift
            ;;
        -i|--interactive)
            DETACH="no"
            shift
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -*)
            echo "Error: Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            CONTAINER_NAME="$1"
            shift
            ;;
    esac
done

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
