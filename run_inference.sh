#!/bin/bash
# LLaMA-Factory Setup and Inference/API Launcher
# This script installs dependencies and starts the API server

set -e

MODE="${1:-api}"  # api or chat
CONFIG="${2:-itri/inference/gpt_lora_120b_sft.yaml}"

echo "=========================================="
echo "LLaMA-Factory Setup & Launch"
echo "=========================================="
echo "Mode: $MODE"
echo "Config: $CONFIG"
echo "=========================================="

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
fi

# Install LLaMA-Factory if not already installed
NEEDS_INSTALL=false

# Check if llamafactory module is importable (most reliable check)
if python3 -c "import llamafactory" 2>/dev/null; then
    echo "✓ LLaMA-Factory already installed (module found)"
elif command -v llamafactory-cli &> /dev/null; then
    echo "✓ LLaMA-Factory already installed (found in PATH)"
else
    NEEDS_INSTALL=true
fi

if [ "$NEEDS_INSTALL" = true ]; then
    echo ""
    echo "Installing LLaMA-Factory..."
    echo "This may take 5-10 minutes, please be patient..."
    
    pip install -e ".[torch,metrics]" --no-build-isolation
    
    # Fix all dependency version issues
    echo ""
    echo "Fixing dependency versions..."
    pip uninstall -y torchao 2>/dev/null || true
    pip install --force-reinstall \
        transformers==4.57.1 \
        peft==0.17.1 \
        accelerate==1.11.0 \
        torchvision
    
    echo "✓ Installation complete"
fi

# Install benchmark dependencies if needed
echo ""
echo "Checking benchmark dependencies..."
python3 -c "import datasets, requests, tqdm" 2>/dev/null || {
    echo "Installing benchmark dependencies..."
    pip install -q datasets requests tqdm
    echo "✓ Benchmark dependencies installed"
}

# Verify llamafactory-cli is now available
echo ""
echo "Verifying llamafactory-cli installation..."

# Determine which llamafactory-cli to use (check system paths first for container compatibility)
# Use python3 -m llamafactory.cli to avoid shebang path issues in containers
if command -v llamafactory-cli &> /dev/null; then
    LLAMAFACTORY_CMD="llamafactory-cli"
    echo "✓ Found: llamafactory-cli (in PATH)"
elif [ -f /usr/local/bin/llamafactory-cli ]; then
    LLAMAFACTORY_CMD="python3 /usr/local/bin/llamafactory-cli"
    echo "✓ Found: /usr/local/bin/llamafactory-cli (using python3)"
elif [ -f .venv/bin/llamafactory-cli ]; then
    # Use python3 directly to avoid shebang path issues
    LLAMAFACTORY_CMD="python3 .venv/bin/llamafactory-cli"
    echo "✓ Found: .venv/bin/llamafactory-cli (using python3)"
elif python3 -c "import llamafactory" 2>/dev/null; then
    # If package is installed, use module execution
    LLAMAFACTORY_CMD="python3 -m llamafactory.cli"
    echo "✓ Found: llamafactory package (using python3 -m)"
else
    echo "ERROR: llamafactory-cli not found after installation"
    echo "Searched in:"
    echo "  - PATH (command -v llamafactory-cli)"
    echo "  - /usr/local/bin/llamafactory-cli"
    echo "  - .venv/bin/llamafactory-cli"
    echo "  - Python module (python3 -m llamafactory.cli)"
    echo ""
    echo "Trying to locate it..."
    find /usr/local -name "llamafactory-cli" 2>/dev/null || true
    find ~/.local -name "llamafactory-cli" 2>/dev/null || true
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG" ]; then
    echo "ERROR: Config file not found: $CONFIG"
    exit 1
fi

echo ""
echo "=========================================="

# Run based on mode
if [ "$MODE" = "api" ]; then
    echo "Starting API Server..."
    echo "=========================================="
    echo ""
    echo "Using: $LLAMAFACTORY_CMD"
    echo "API will be available at: http://localhost:8000"
    echo "Press Ctrl+C to stop"
    echo ""
    
    $LLAMAFACTORY_CMD api "$CONFIG"
    
elif [ "$MODE" = "chat" ]; then
    echo "Starting Interactive Chat..."
    echo "=========================================="
    echo ""
    echo "Using: $LLAMAFACTORY_CMD"
    
    $LLAMAFACTORY_CMD chat "$CONFIG"
    
else
    echo "ERROR: Invalid mode '$MODE'"
    echo "Usage: $0 [api|chat] [config_file]"
    exit 1
fi
