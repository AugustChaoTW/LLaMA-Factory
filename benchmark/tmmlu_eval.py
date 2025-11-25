#!/usr/bin/env python3
"""
TMMLU (Taiwan Mandarin Language Understanding) Benchmark Evaluation
Integrates with llamafactory-cli API for model evaluation
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import requests
import time
from tqdm import tqdm
from datasets import load_dataset

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class LlamaFactoryAPIClient:
    """Client for llamafactory-cli API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.chat_endpoint = f"{base_url}/v1/chat/completions"
        
    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.1) -> Optional[str]:
        """Generate response from the model via API"""
        payload = {
            "model": "default",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            response = requests.post(self.chat_endpoint, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"API Error: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check if API is available"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False


class TMMLUEvaluator:
    """TMMLU Benchmark Evaluator"""
    
    def __init__(self, api_client: LlamaFactoryAPIClient, output_dir: str = "benchmark/results"):
        self.api_client = api_client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_tmmlu_dataset(self, split: str = "test", subjects: Optional[List[str]] = None) -> Dict:
        """Load TMMLU+ dataset from HuggingFace"""
        print(f"Loading TMMLU+ dataset (split: {split})...")
        
        # Available subjects in TMMLU+
        all_subjects = [
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
        
        # Use specified subjects or all subjects
        subjects_to_load = subjects if subjects else all_subjects[:5]  # Default to first 5 for testing
        
        print(f"Loading {len(subjects_to_load)} subjects...")
        
        all_data = []
        try:
            for subject in subjects_to_load:
                try:
                    dataset = load_dataset("ikala/tmmluplus", subject, split=split)
                    # Add subject name to each item
                    for item in dataset:
                        item['subject'] = subject
                        all_data.append(item)
                    print(f"  ✓ Loaded {subject}: {len(dataset)} questions")
                except Exception as e:
                    print(f"  ✗ Failed to load {subject}: {e}")
                    continue
            
            print(f"Total questions loaded: {len(all_data)}")
            return all_data
            
        except Exception as e:
            print(f"Error loading dataset: {e}")
            return None
    
    def format_question(self, item: Dict) -> str:
        """Format a TMMLU question as a prompt"""
        question = item["question"]
        
        # Get choices from A, B, C, D keys
        choices = [
            item.get("A", ""),
            item.get("B", ""),
            item.get("C", ""),
            item.get("D", "")
        ]
        
        # Format choices as A, B, C, D
        formatted_choices = []
        for idx, choice in enumerate(choices):
            if choice:  # Only include non-empty choices
                label = chr(65 + idx)  # A, B, C, D
                formatted_choices.append(f"{label}. {choice}")
        
        prompt = f"""請回答以下選擇題，只需要回答選項字母（A、B、C或D）。

問題：{question}

選項：
{chr(10).join(formatted_choices)}

答案："""
        
        return prompt
    
    def extract_answer(self, response: str) -> Optional[str]:
        """Extract answer choice (A, B, C, D) from model response"""
        if not response:
            return None
        
        # Look for A, B, C, or D in the response
        response_upper = response.strip().upper()
        
        # Check if response starts with a choice
        if response_upper and response_upper[0] in ['A', 'B', 'C', 'D']:
            return response_upper[0]
        
        # Look for choice in the response
        for choice in ['A', 'B', 'C', 'D']:
            if choice in response_upper:
                return choice
        
        return None
    
    def evaluate_sample(self, item: Dict) -> Dict:
        """Evaluate a single sample"""
        prompt = self.format_question(item)
        response = self.api_client.generate(prompt, max_tokens=10, temperature=0.1)
        predicted = self.extract_answer(response)
        
        # Get correct answer (already in A/B/C/D format)
        correct = item["answer"].upper()
        
        is_correct = (predicted == correct) if predicted else False
        
        return {
            "question": item["question"],
            "subject": item.get("subject", "unknown"),
            "correct_answer": correct,
            "predicted_answer": predicted,
            "raw_response": response,
            "is_correct": is_correct
        }
    
    def evaluate(self, max_samples: Optional[int] = None, subjects: Optional[List[str]] = None) -> Dict:
        """Run full evaluation"""
        print("Starting TMMLU evaluation...")
        
        # Check API health
        if not self.api_client.health_check():
            print("ERROR: API is not available. Please start the llamafactory-cli API server first.")
            print("Run: llamafactory-cli api <your_config.yaml>")
            return None
        
        print("API health check passed ✓")
        
        # Load dataset
        dataset = self.load_tmmlu_dataset(subjects=subjects)
        if dataset is None or len(dataset) == 0:
            print("ERROR: Failed to load dataset")
            return None
        
        print(f"Dataset loaded: {len(dataset)} samples")
        
        # Limit samples if specified
        if max_samples:
            dataset = dataset[:min(max_samples, len(dataset))]
            print(f"Evaluating {len(dataset)} samples")
        
        # Evaluate
        results = []
        correct_count = 0
        subject_stats = {}
        
        for item in tqdm(dataset, desc="Evaluating"):
            result = self.evaluate_sample(item)
            results.append(result)
            
            if result["is_correct"]:
                correct_count += 1
            
            # Track per-subject stats
            subject = result["subject"]
            if subject not in subject_stats:
                subject_stats[subject] = {"correct": 0, "total": 0}
            subject_stats[subject]["total"] += 1
            if result["is_correct"]:
                subject_stats[subject]["correct"] += 1
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
        
        # Calculate metrics
        total = len(results)
        accuracy = correct_count / total if total > 0 else 0
        
        # Calculate per-subject accuracy
        for subject in subject_stats:
            stats = subject_stats[subject]
            stats["accuracy"] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        
        evaluation_results = {
            "overall_accuracy": accuracy,
            "correct": correct_count,
            "total": total,
            "subject_stats": subject_stats,
            "detailed_results": results
        }
        
        return evaluation_results
    
    def save_results(self, results: Dict, filename: str = "tmmlu_results.json"):
        """Save evaluation results to file"""
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to: {output_path}")
        
    def print_summary(self, results: Dict):
        """Print evaluation summary"""
        print("\n" + "="*60)
        print("TMMLU EVALUATION RESULTS")
        print("="*60)
        print(f"Overall Accuracy: {results['overall_accuracy']:.2%}")
        print(f"Correct: {results['correct']} / {results['total']}")
        print("\nPer-Subject Results:")
        print("-"*60)
        
        # Sort subjects by accuracy
        subject_stats = results['subject_stats']
        sorted_subjects = sorted(subject_stats.items(), 
                                key=lambda x: x[1]['accuracy'], 
                                reverse=True)
        
        for subject, stats in sorted_subjects:
            print(f"{subject:30s}: {stats['accuracy']:6.2%} ({stats['correct']}/{stats['total']})")
        
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="TMMLU Benchmark Evaluation")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000",
                       help="LlamaFactory API base URL")
    parser.add_argument("--max-samples", type=int, default=None,
                       help="Maximum number of samples to evaluate (for testing)")
    parser.add_argument("--subjects", type=str, nargs="+", default=None,
                       help="Specific subjects to evaluate")
    parser.add_argument("--output-dir", type=str, default="benchmark/results",
                       help="Output directory for results")
    parser.add_argument("--output-file", type=str, default="tmmlu_results.json",
                       help="Output filename for results")
    
    args = parser.parse_args()
    
    # Initialize API client
    api_client = LlamaFactoryAPIClient(base_url=args.api_url)
    
    # Initialize evaluator
    evaluator = TMMLUEvaluator(api_client, output_dir=args.output_dir)
    
    # Run evaluation
    results = evaluator.evaluate(max_samples=args.max_samples, subjects=args.subjects)
    
    if results:
        # Print summary
        evaluator.print_summary(results)
        
        # Save results
        evaluator.save_results(results, filename=args.output_file)
    else:
        print("Evaluation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
