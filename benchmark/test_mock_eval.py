#!/usr/bin/env python3
"""
Mock evaluation test - simulates API responses to test the evaluation pipeline
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from tqdm import tqdm

def mock_evaluate():
    """Run a mock evaluation with simulated responses"""
    print("="*60)
    print("TMMLU Mock Evaluation Test")
    print("="*60)
    print("\nThis test simulates the evaluation pipeline without requiring")
    print("an actual API server. It uses random answers for demonstration.\n")
    
    # Load a small dataset
    subject = "physics"
    print(f"Loading {subject} dataset...")
    dataset = load_dataset("ikala/tmmluplus", subject, split="test")
    
    # Limit to 10 samples for quick test
    samples = list(dataset)[:10]
    print(f"Testing with {len(samples)} samples\n")
    
    # Simulate evaluation
    results = []
    correct_count = 0
    
    for idx, item in enumerate(tqdm(samples, desc="Evaluating")):
        # Format question
        question = item["question"]
        choices = [item.get("A", ""), item.get("B", ""), item.get("C", ""), item.get("D", "")]
        correct_answer = item["answer"].upper()
        
        # Simulate model response (for demo, just use correct answer for first 7)
        simulated_response = correct_answer if idx < 7 else "A"
        
        is_correct = (simulated_response == correct_answer)
        if is_correct:
            correct_count += 1
        
        results.append({
            "question": question[:50] + "...",
            "subject": subject,
            "correct_answer": correct_answer,
            "predicted_answer": simulated_response,
            "is_correct": is_correct
        })
    
    # Print results
    accuracy = correct_count / len(samples)
    
    print("\n" + "="*60)
    print("MOCK EVALUATION RESULTS")
    print("="*60)
    print(f"Overall Accuracy: {accuracy:.2%}")
    print(f"Correct: {correct_count} / {len(samples)}")
    print("\nDetailed Results:")
    print("-"*60)
    
    for i, result in enumerate(results, 1):
        status = "✓" if result["is_correct"] else "✗"
        print(f"{i}. {status} Predicted: {result['predicted_answer']}, Correct: {result['correct_answer']}")
    
    print("="*60)
    print("\n✓ Mock evaluation completed successfully!")
    print("\nTo run real evaluation:")
    print("  1. Ensure API server is running on port 8000")
    print("  2. Run: .venv/bin/python3 benchmark/tmmlu_eval.py --max-samples 10")
    
    # Save mock results
    output_dir = Path("benchmark/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "mock_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "overall_accuracy": accuracy,
            "correct": correct_count,
            "total": len(samples),
            "subject_stats": {subject: {"correct": correct_count, "total": len(samples), "accuracy": accuracy}},
            "detailed_results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nMock results saved to: {output_file}")

if __name__ == "__main__":
    mock_evaluate()
