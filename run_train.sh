#!/bin/bash
# LLaMA-Factory Training Script
# Automatically installs dependencies and runs model training

# Show help message
show_help() {
    cat << EOF
Usage: bash run_train.sh [OPTIONS] [CONFIG_FILE]

Train LLaMA-Factory models with automatic dependency installation.

OPTIONS:
    -h, --help          Show this help message and exit
    -s, --skip-install  Skip LLaMA-Factory installation check
    -c, --config FILE   Specify training config file (default: gpt120b_lora_sft.yaml)

CONFIG_FILE:
    Path to training YAML configuration file. If not specified, uses default.

Available configs:
    itri/train_lora/llama3_lora_sft.yaml    - Llama3 LoRA SFT
    itri/train_lora/llama33_lora_sft.yaml   - Llama3.3 LoRA SFT
    itri/train_lora/gpt_lora_sft.yaml       - GPT LoRA SFT
    itri/train_lora/gpt120b_lora_sft.yaml   - GPT 120B LoRA SFT (default)

EXAMPLES:
    # Use default config (GPT 120B)
    bash run_train.sh

    # Train with specific config
    bash run_train.sh itri/train_lora/llama3_lora_sft.yaml

    # Skip installation check
    bash run_train.sh --skip-install itri/train_lora/gpt_lora_sft.yaml

ENVIRONMENT:
    WANDB_API_KEY    Set Weights & Biases API key (default: auto-configured)

EOF
}

# Parse arguments
SKIP_INSTALL=false
CONFIG_FILE="itri/train_lora/gpt120b_lora_sft.yaml"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -*)
            echo "Error: Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            CONFIG_FILE="$1"
            shift
            ;;
    esac
done

# Install LLaMA-Factory if not already installed
if [ "$SKIP_INSTALL" = false ] && [ ! -f "/usr/local/bin/llamafactory-cli" ]; then
  echo "Installing LLaMA-Factory..."
  pip install -e ".[torch,metrics]" --no-build-isolation

  # Fix all dependency version issues
  echo "Fixing dependency versions..."
  pip uninstall -y torchao 2>/dev/null || true
  pip install --force-reinstall \
    transformers==4.57.1 \
    peft==0.17.1 \
    accelerate==1.11.0 \
    torchvision \
    wandb \
    triton>=3.4.0 \
    git+https://github.com/triton-lang/triton.git@main#subdirectory=python/triton_kernels


  echo "✓ Installation complete"
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    echo "Use --help to see available configs"
    exit 1
fi

export WANDB_API_KEY=16ea8ae3fd4af15a25099894b5f6928f463085b2

# Run training
echo "=========================================="
echo "Starting training with config: $CONFIG_FILE"
echo "=========================================="
llamafactory-cli train "$CONFIG_FILE"
