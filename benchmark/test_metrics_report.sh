#!/bin/bash
# Quick test script for Docker API evaluation with metrics reporting

echo "Testing TMMLU evaluation with Docker API and metrics reporting..."
echo ""

# Get Docker container IP
CONTAINER_IP=$(sudo docker inspect gracious_archimedes --format='{{.NetworkSettings.IPAddress}}' 2>/dev/null)

if [ -z "$CONTAINER_IP" ]; then
    echo "ERROR: Container not found"
    exit 1
fi

echo "Container IP: $CONTAINER_IP"
echo "Running evaluation with 5 samples..."
echo ""

# Run evaluation directly (without starting new API server)
RESULT_FILE="benchmark/results/test_metrics_$(date +%Y%m%d_%H%M%S).json"

.venv/bin/python3 benchmark/tmmlu_eval.py \
    --api-url "http://$CONTAINER_IP:8000" \
    --max-samples 5 \
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
    exit $EVAL_EXIT_CODE
fi

# Report evaluation metrics
if [ -f "$RESULT_FILE" ]; then
    echo ""
    echo "📊 Evaluation Metrics Report"
    echo "=========================================="
    
    # Extract metrics using python
    .venv/bin/python3 << EOF
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
fi

echo ""
