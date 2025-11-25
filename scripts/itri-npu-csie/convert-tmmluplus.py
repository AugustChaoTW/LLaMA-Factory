#!/usr/bin/env python3
"""
Convert TMMLU+ benchmark dataset to LLaMA-Factory training format

This script loads the ikala/tmmluplus dataset from HuggingFace and converts it
into a JSON format suitable for training with LLaMA-Factory.

Output format:
[
    {
        "instruction": "問題內容",
        "input": "",
        "output": "正確答案及解釋"
    },
    ...
]
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' library not found. Please install it:")
    print("  pip install datasets")
    sys.exit(1)



# All available subjects in TMMLU+
ALL_SUBJECTS = [
    'engineering_math', 'dentistry', 'traditional_chinese_medicine_clinical_medicine',
    'clinical_psychology', 'technical', 'culinary_skills', 'mechanical', 'logic_reasoning',
    'real_estate', 'general_principles_of_law', 'finance_banking', 'anti_money_laundering',
    'ttqav2', 'marketing_management', 'business_management', 'organic_chemistry',
    'advance_chemistry', 'physics', 'secondary_physics', 'human_behavior',
    'national_protection', 'jce_humanities', 'politic_science', 'agriculture',
    'official_document_management', 'financial_analysis', 'pharmacy', 'educational_psychology',
    'statistics_and_machine_learning', 'management_accounting', 'introduction_to_law',
    'computer_science', 'veterinary_pathology', 'accounting', 'fire_science',
    'optometry', 'insurance_studies', 'pharmacology', 'taxation', 'trust_practice',
    'geography_of_taiwan', 'physical_education', 'auditing', 'administrative_law',
    'education_(profession_level)', 'economics', 'veterinary_pharmacology', 'nautical_science',
    'occupational_therapy_for_psychological_disorders', 'basic_medical_science', 'macroeconomics',
    'trade', 'chinese_language_and_literature', 'tve_design', 'junior_science_exam',
    'junior_math_exam', 'junior_chinese_exam', 'junior_social_studies', 'tve_mathematics',
    'tve_chinese_language', 'tve_natural_sciences', 'junior_chemistry', 'music',
    'education', 'three_principles_of_people', 'taiwanese_hokkien'
]


def format_question_for_training(item: Dict, subject: str) -> Dict:
    """
    Convert a TMMLU+ item to LLaMA-Factory training format
    
    Args:
        item: Dataset item with keys: question, A, B, C, D, answer
        subject: Subject name
        
    Returns:
        Dictionary in LLaMA-Factory format with instruction, input, output
    """
    question = item["question"]
    
    # Get choices from A, B, C, D keys
    choices = {
        "A": item.get("A", ""),
        "B": item.get("B", ""),
        "C": item.get("C", ""),
        "D": item.get("D", "")
    }
    
    # Format choices
    formatted_choices = []
    for label in ["A", "B", "C", "D"]:
        if choices[label]:
            formatted_choices.append(f"{label}. {choices[label]}")
    
    # Get correct answer
    correct_answer = item["answer"].upper()
    correct_text = choices.get(correct_answer, "")
    
    # Create instruction (the question with choices)
    instruction = f"""請回答以下選擇題。

問題：{question}

選項：
{chr(10).join(formatted_choices)}"""
    
    # Create output (the correct answer with explanation)
    output = f"答案是 {correct_answer}。{correct_text}"
    
    return {
        "instruction": instruction,
        "input": "",
        "output": output
    }


def load_and_convert_dataset(
    subjects: List[str] = None,
    split: str = "test",
    output_file: str = "data/ikala_tmmluplus.json"
) -> None:
    """
    Load TMMLU+ dataset and convert to training format
    
    Args:
        subjects: List of subjects to load (None = all subjects)
        split: Dataset split to use (default: "test")
        output_file: Output JSON file path
    """
    subjects_to_load = subjects if subjects else ALL_SUBJECTS
    
    print(f"Converting TMMLU+ dataset to training format")
    print(f"Subjects: {len(subjects_to_load)}")
    print(f"Split: {split}")
    print(f"Output: {output_file}")
    print("=" * 60)
    
    all_training_data = []
    failed_subjects = []
    
    for idx, subject in enumerate(subjects_to_load, 1):
        try:
            print(f"[{idx}/{len(subjects_to_load)}] Loading {subject}...")
            
            # Load dataset for this subject
            dataset = load_dataset("ikala/tmmluplus", subject, split=split)
            
            # Convert each item
            for item in dataset:
                training_item = format_question_for_training(item, subject)
                all_training_data.append(training_item)
            
            print(f"  ✓ {subject}: {len(dataset)} questions")
            
        except Exception as e:
            print(f"  ✗ {subject}: Failed - {e}")
            failed_subjects.append(subject)
            continue

    
    print("=" * 60)
    print(f"Total training samples: {len(all_training_data)}")
    print(f"Successfully loaded: {len(subjects_to_load) - len(failed_subjects)}/{len(subjects_to_load)} subjects")
    
    if failed_subjects:
        print(f"Failed subjects: {', '.join(failed_subjects)}")
    
    # Save to JSON file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_training_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved to: {output_path}")
    print(f"  File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Print sample
    if all_training_data:
        print("\nSample training data:")
        print("=" * 60)
        sample = all_training_data[0]
        print(f"Instruction:\n{sample['instruction']}\n")
        print(f"Output:\n{sample['output']}")
        print("=" * 60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert TMMLU+ dataset to LLaMA-Factory training format"
    )
    parser.add_argument(
        "--subjects",
        type=str,
        nargs="+",
        default=None,
        help="Specific subjects to convert (default: all subjects)"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Dataset split to use (default: test)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/ikala_tmmluplus.json",
        help="Output JSON file path (default: data/ikala_tmmluplus.json)"
    )
    
    args = parser.parse_args()
    
    # Convert dataset
    load_and_convert_dataset(
        subjects=args.subjects,
        split=args.split,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
