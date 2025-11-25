#!/bin/bash
# Helper script to expose Docker container API port
# This script provides easy access to the llamafactory-cli API running in Docker

CONTAINER_NAME="${1:-gracious_archimedes}"

echo "=========================================="
echo "Docker API Port Exposure Helper"
echo "=========================================="

# Get container IP
CONTAINER_IP=$(sudo docker inspect "$CONTAINER_NAME" --format='{{.NetworkSettings.IPAddress}}' 2>/dev/null)

if [ -z "$CONTAINER_IP" ]; then
    echo "ERROR: Container '$CONTAINER_NAME' not found or not running"
    echo "Available containers:"
    sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    exit 1
fi

echo "Container: $CONTAINER_NAME"
echo "Container IP: $CONTAINER_IP"
echo ""

# Check if API is running
echo "Checking API status..."
API_RESPONSE=$(sudo docker exec "$CONTAINER_NAME" curl -s http://localhost:8000/v1/models 2>/dev/null)

if [ -z "$API_RESPONSE" ]; then
    echo "WARNING: API not responding on port 8000 inside container"
    echo "Make sure llamafactory-cli api is running inside the container"
    exit 1
fi

echo "✓ API is running inside container"
echo ""

# Test from host
echo "Testing API access from host..."
HOST_RESPONSE=$(curl -s http://$CONTAINER_IP:8000/v1/models 2>/dev/null)

if [ -z "$HOST_RESPONSE" ]; then
    echo "ERROR: Cannot access API from host"
    exit 1
fi

echo "✓ API is accessible from host"
echo ""

echo "=========================================="
echo "API Access Information"
echo "=========================================="
echo "Direct access URL: http://$CONTAINER_IP:8000"
echo ""
echo "To run TMMLU evaluation:"
echo "  .venv/bin/python3 benchmark/tmmlu_eval.py \\"
echo "    --api-url http://$CONTAINER_IP:8000 \\"
echo "    --max-samples 100"
echo ""
echo "To test API:"
echo "  curl http://$CONTAINER_IP:8000/v1/models"
echo ""
echo "=========================================="
