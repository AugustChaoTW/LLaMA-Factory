#!/usr/bin/env python3
"""
Quick test script to verify TMMLU dataset loading and formatting
without requiring API server
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset

def test_dataset_loading():
    """Test loading a single subject"""
    print("Testing TMMLU+ dataset loading...")
    print("="*60)
    
    # Load a small subject for testing
    subject = "physics"
    print(f"\nLoading subject: {subject}")
    
    dataset = load_dataset("ikala/tmmluplus", subject, split="test")
    print(f"✓ Loaded {len(dataset)} questions")
    
    # Show sample
    sample = dataset[0]
    print(f"\nSample question:")
    print(f"  Question: {sample['question'][:80]}...")
    print(f"  A: {sample['A']}")
    print(f"  B: {sample['B']}")
    print(f"  C: {sample['C']}")
    print(f"  D: {sample['D']}")
    print(f"  Correct Answer: {sample['answer']}")
    
    # Test formatting
    print(f"\n" + "="*60)
    print("Testing question formatting...")
    print("="*60)
    
    choices = [sample.get("A", ""), sample.get("B", ""), sample.get("C", ""), sample.get("D", "")]
    formatted_choices = []
    for idx, choice in enumerate(choices):
        if choice:
            label = chr(65 + idx)
            formatted_choices.append(f"{label}. {choice}")
    
    prompt = f"""請回答以下選擇題，只需要回答選項字母（A、B、C或D）。

問題：{sample['question']}

選項：
{chr(10).join(formatted_choices)}

答案："""
    
    print(prompt)
    print("="*60)
    print("✓ All tests passed!")
    print("\nTo run full evaluation:")
    print("  1. Start API: llamafactory-cli api itri/inference/gpt_lora_120b_sft.yaml")
    print("  2. Run eval: bash benchmark/run_tmmlu_eval.sh")
    

if __name__ == "__main__":
    test_dataset_loading()
