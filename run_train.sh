#!/bin/bash

# Install LLaMA-Factory if not already installed
if [ ! -f "/usr/local/bin/llamafactory-cli" ]; then
  echo "Installing LLaMA-Factory..."
  pip install -e ".[torch,metrics]" --no-build-isolation

  # Fix all dependency version issues
  echo "Fixing dependency versions..."
  pip uninstall -y torchao
  pip install --force-reinstall \
    transformers==4.57.1 \
    peft==0.17.1 \
    accelerate==1.11.0 \
    torchvision

fi



# Run training
echo "Starting training..."
# llamafactory-cli train itri/train_lora/llama3_lora_sft.yaml
# llamafactory-cli train itri/train_lora/llama33_lora_sft.yaml
# llamafactory-cli train itri/train_lora/gpt_lora_sft.yaml
llamafactory-cli train itri/train_lora/gpt120b_lora_sft.yaml
