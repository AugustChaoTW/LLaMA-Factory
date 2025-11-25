#!/usr/bin/env python3
"""
Convert DEID thinking datasets to LLaMA-Factory training format

This script loads the deid thinking datasets (account, device, ip, mac, name, org)
and converts them into instruction-tuning format suitable for LLaMA and GPT models.

The thinking datasets contain:
- user: request for de-identification
- assistant_thought: reasoning process
- assistant: de-identified output with mapping table

Output format for LLaMA-Factory:
{
    "instruction": "user request",
    "input": "",
    "output": "assistant response (with thinking process)"
}
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict

# Dataset files to process
THINKING_FILES = [
    'account_daraset_thinking.json',  # Note: typo in original filename
    'device_dataset_thinking.json',
    'ip_dataset_thinking.json',
    'mac_dataset_thinking.json',
    'name_dataset_thinking.json',
    'org_dataset_thinking.json'
]

DEID_DIR = 'data/npu-csie/deid'
OUTPUT_FILE = 'data/npu-csie/deid.json'


def convert_thinking_to_training(messages: List[Dict]) -> Dict:
    """
    Convert a thinking dataset sample to training format
    
    Args:
        messages: List of message dicts with role and content
        
    Returns:
        Training sample with instruction, input, output
    """
    user_content = ""
    thought_content = ""
    assistant_content = ""
    
    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        if role == 'user':
            user_content = content
        elif role == 'assistant_thought':
            thought_content = content
        elif role == 'assistant':
            assistant_content = content
    
    # Combine thought and assistant response
    # Format: <thinking>thought</thinking>\nassistant_response
    if thought_content:
        output = f"<thinking>{thought_content}</thinking>\n\n{assistant_content}"
    else:
        output = assistant_content
    
    return {
        "instruction": user_content,
        "input": "",
        "output": output
    }


def load_and_convert_datasets(
    deid_dir: str = DEID_DIR,
    output_file: str = OUTPUT_FILE
) -> None:
    """
    Load all thinking datasets and convert to training format
    
    Args:
        deid_dir: Directory containing thinking dataset files
        output_file: Output JSON file path
    """
    print(f"Converting DEID thinking datasets to training format")
    print(f"Source directory: {deid_dir}")
    print(f"Output file: {output_file}")
    print("=" * 60)
    
    all_training_data = []
    stats = {}
    
    for filename in THINKING_FILES:
        filepath = os.path.join(deid_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"  ✗ {filename}: File not found")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                print(f"  ✗ {filename}: Empty file")
                continue
            
            # Convert each sample
            converted_count = 0
            for item in data:
                messages = item.get('messages', [])
                if messages:
                    training_sample = convert_thinking_to_training(messages)
                    all_training_data.append(training_sample)
                    converted_count += 1
            
            stats[filename] = converted_count
            print(f"  ✓ {filename}: {converted_count} samples")
            
        except json.JSONDecodeError as e:
            print(f"  ✗ {filename}: JSON decode error - {e}")
            continue
        except Exception as e:
            print(f"  ✗ {filename}: Error - {e}")
            continue
    
    print("=" * 60)
    print(f"Total training samples: {len(all_training_data)}")
    print(f"Successfully loaded: {len(stats)}/{len(THINKING_FILES)} files")
    
    # Save to JSON file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_training_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved to: {output_path}")
    print(f"  File size: {output_path.stat().st_size / 1024:.2f} KB")
    
    # Print sample
    if all_training_data:
        print("\nSample training data:")
        print("=" * 60)
        sample = all_training_data[0]
        print(f"Instruction:\n{sample['instruction'][:200]}...\n")
        print(f"Output:\n{sample['output'][:300]}...")
        print("=" * 60)
    
    # Print statistics
    print("\nDataset Statistics:")
    for filename, count in sorted(stats.items()):
        category = filename.replace('_dataset_thinking.json', '').replace('_daraset_thinking.json', '')
        print(f"  {category}: {count} samples")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert DEID thinking datasets to LLaMA-Factory training format"
    )
    parser.add_argument(
        "--deid-dir",
        type=str,
        default=DEID_DIR,
        help=f"Directory containing thinking dataset files (default: {DEID_DIR})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILE,
        help=f"Output JSON file path (default: {OUTPUT_FILE})"
    )
    
    args = parser.parse_args()
    
    # Convert datasets
    load_and_convert_datasets(
        deid_dir=args.deid_dir,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
