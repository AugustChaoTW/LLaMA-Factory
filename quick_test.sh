#!/bin/bash
# Quick test script - run this in your newgrp docker session

echo "Testing Docker permissions..."
docker ps > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Docker permission error!"
    echo "Please run: newgrp docker"
    echo "Then run this script again"
    exit 1
fi

echo "✅ Docker permissions OK"
echo ""

# Clean up any existing container
echo "Cleaning up old containers..."
docker stop llama-factory-benchmark 2>/dev/null || true
docker rm llama-factory-benchmark 2>/dev/null || true

echo "Starting container..."
docker run -d \
    --name llama-factory-benchmark \
    --gpus all \
    --ipc=host \
    --ulimit memlock=-1 \
    --ulimit stack=67108864 \
    -v $(pwd):/workspace/LLaMA-Factory \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -w /workspace/LLaMA-Factory \
    nvcr.io/nvidia/pytorch:25.10-py3 \
    tail -f /dev/null

echo "✅ Container started"
echo ""

echo "Installing LLaMA-Factory in container..."
echo "This will take 5-10 minutes..."
echo ""

docker exec llama-factory-benchmark bash -c "
    echo '→ Installing LLaMA-Factory...'
    pip install -e '.[torch,metrics]' --no-build-isolation 2>&1 | tail -5
    
    echo '→ Fixing dependencies...'
    pip uninstall -y torchao 2>/dev/null || true
    pip install --force-reinstall transformers==4.57.1 peft==0.17.1 accelerate==1.11.0 torchvision 2>&1 | tail -3
    
    echo '→ Installing benchmark dependencies...'
    pip install -q datasets requests tqdm
    
    echo '✅ Installation complete'
    
    # Verify installation
    if [ -f /usr/local/bin/llamafactory-cli ]; then
        echo '✅ llamafactory-cli found at /usr/local/bin/llamafactory-cli'
    else
        echo '❌ llamafactory-cli not found!'
        exit 1
    fi
"

if [ $? -ne 0 ]; then
    echo "❌ Installation failed"
    exit 1
fi

echo ""
echo "Starting API server..."
docker exec -d llama-factory-benchmark bash -c "llamafactory-cli api itri/inference/gpt_lora_120b_sft.yaml > /tmp/api.log 2>&1"

echo "Waiting for API to be ready..."
for i in {1..60}; do
    if docker exec llama-factory-benchmark curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    sleep 2
    echo -n "."
done

echo ""
echo ""
echo "Running TMMLU evaluation (10 samples)..."
docker exec -it llama-factory-benchmark bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 10 yes

echo ""
echo "Cleaning up..."
docker stop llama-factory-benchmark
docker rm llama-factory-benchmark

echo "✅ Done!"
