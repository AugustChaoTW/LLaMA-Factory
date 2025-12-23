#!/usr/bin/env python3
"""
Script to compile all *.txt files from the deid directory into a single trainable dataset.
This script reads all text files and creates a LLaMA-Factory compatible JSON dataset.
It can optionally use an LLM API to generate thinking sections for better training data.
Supports parallel processing for faster API calls.
"""

import json
import os
import glob
import time
import requests
import signal
import sys
import uuid
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from loguru import logger


# API Configuration
API_URL = "http://localhost:8000/v1/chat/completions"
API_MODEL = "gpt-oss-120b"
API_TEMPERATURE = 0.6
API_MAX_TOKENS = 2048
API_TIMEOUT = 300  # seconds
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 2  # seconds

# Parallel Processing Configuration
# GB300 has excellent parallel processing capabilities
MAX_WORKERS = 32  # Number of concurrent API calls (optimized for GB300)
PROGRESS_UPDATE_INTERVAL = 5  # Update progress every N completions

# Global state for graceful shutdown
shutdown_requested = False
progress_lock = Lock()
completed_count = 0

# Generate unique RUN_ID for this execution
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print("\n\n⚠ Interrupt received! Finishing current requests and saving progress...")
    print("   Press Ctrl+C again to force quit (may lose data)")
    shutdown_requested = True
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(1))


def call_llm_api(prompt, retry_count=0, record_id=None):
    """
    Call the LLM API to generate a response with thinking section.
    
    Args:
        prompt: The user prompt to send to the API
        retry_count: Current retry attempt number
        record_id: Identifier for logging purposes
    
    Returns:
        The assistant's response content, or None if failed
    """
    logger.debug(f"[{record_id}] Calling API (attempt {retry_count + 1}/{API_RETRY_ATTEMPTS})")
    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "model": API_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": API_TEMPERATURE,
                "max_tokens": API_MAX_TOKENS
            },
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            logger.success(f"[{record_id}] API call successful, response length: {len(content)} chars")
            return content
        else:
            logger.warning(f"[{record_id}] API error: {response.status_code}")
            print(f"    ⚠ API error: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning(f"[{record_id}] API timeout (attempt {retry_count + 1}/{API_RETRY_ATTEMPTS})")
        print(f"    ⚠ API timeout (attempt {retry_count + 1}/{API_RETRY_ATTEMPTS})")
        if retry_count < API_RETRY_ATTEMPTS - 1:
            time.sleep(API_RETRY_DELAY)
            return call_llm_api(prompt, retry_count + 1, record_id)
        return None
        
    except Exception as e:
        logger.error(f"[{record_id}] API error: {str(e)}")
        print(f"    ⚠ API error: {str(e)}")
        return None


def create_training_example_with_api(text_line, category, instruction, record_idx):
    """
    Create a training example using the API (for parallel processing).
    
    Args:
        text_line: The raw text line from the txt file
        category: The category/type of the data
        instruction: The formatted instruction prompt
        record_idx: Index of this record for logging
    
    Returns:
        A dictionary with the training example, or None if failed
    """
    global shutdown_requested
    
    record_id = f"{category}_{record_idx:04d}"
    logger.info(f"[{record_id}] Processing: {text_line[:50]}...")
    
    if shutdown_requested:
        logger.warning(f"[{record_id}] Skipped due to shutdown request")
        return None
    
    # Call API to generate response
    assistant_response = call_llm_api(instruction, record_id=record_id)
    
    if not assistant_response:
        # Fallback to placeholder
        assistant_response = f"[此為來自 {category}.txt 的原始資料，需要進行去識別化處理]\n\n{text_line}"
        logger.warning(f"[{record_id}] Using fallback placeholder response")
    
    example = {
        "messages": [
            {
                "role": "user",
                "content": instruction
            },
            {
                "role": "assistant",
                "content": assistant_response
            }
        ]
    }
    
    logger.debug(f"[{record_id}] Created training example")
    return example


def create_training_example(text_line, category, use_api=False):
    """
    Create a training example in LLaMA-Factory format.
    
    Args:
        text_line: The raw text line from the txt file
        category: The category/type of the data
        use_api: Whether to use the LLM API (not used in parallel mode)
    
    Returns:
        A dictionary with the training example in messages format
    """
    # Clean the text line
    text_line = text_line.strip()
    
    if not text_line:
        return None
    
    # Create the instruction
    instruction = f"以下內容請幫我去識別化並加上對照表。\n請先在 <thinking> 標籤中思考去識別化的步驟，然後再提供最終結果:\n\n{text_line}"
    
    # Use placeholder response (API mode uses parallel function)
    assistant_response = f"[此為來自 {category}.txt 的原始資料，需要進行去識別化處理]\n\n{text_line}"
    
    example = {
        "messages": [
            {
                "role": "user",
                "content": instruction
            },
            {
                "role": "assistant",
                "content": assistant_response
            }
        ]
    }
    
    return example


def compile_dataset(input_dir, output_file, use_api=False, max_workers=MAX_WORKERS):
    """
    Compile all *.txt files into a single dataset.
    
    Args:
        input_dir: Directory containing the *.txt files
        output_file: Output JSON file path
        use_api: Whether to use the LLM API to generate responses
        max_workers: Number of parallel workers for API calls
    """
    global shutdown_requested, completed_count
    
    # Create output directory for per-file results
    per_file_dir = os.path.join(input_dir, "thinking-gpt120b")
    os.makedirs(per_file_dir, exist_ok=True)
    logger.info(f"Created output directory: {per_file_dir}")
    logger.info(f"RUN_ID: {RUN_ID}")
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Find all .txt files
    txt_files = glob.glob(os.path.join(input_dir, "*.txt"))
    
    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        logger.error(f"No .txt files found in {input_dir}")
        return
    
    print(f"Found {len(txt_files)} .txt files:")
    logger.info(f"Found {len(txt_files)} .txt files")
    for txt_file in sorted(txt_files):
        print(f"  - {os.path.basename(txt_file)}")
        logger.info(f"  - {os.path.basename(txt_file)}")
    
    if use_api:
        print(f"\n⚡ API Mode: Enabled (Parallel Processing)")
        print(f"   API URL: {API_URL}")
        print(f"   Model: {API_MODEL}")
        print(f"   Temperature: {API_TEMPERATURE}")
        print(f"   Max Tokens: {API_MAX_TOKENS}")
        print(f"   Max Workers: {max_workers} concurrent requests")
        print(f"\n⚠ This will make API calls in parallel for faster processing!")
        logger.info(f"API Mode: Enabled, Max Workers: {max_workers}")
        
        # Test API connection
        print(f"\nTesting API connection...")
        test_response = call_llm_api("Hello", record_id="test_connection")
        if test_response:
            print(f"✓ API connection successful!")
            logger.success("API connection test successful")
        else:
            print(f"✗ API connection failed! Falling back to placeholder mode.")
            logger.error("API connection test failed, falling back to placeholder mode")
            use_api = False
    else:
        print(f"\n📝 API Mode: Disabled (using placeholder responses)")
        logger.info("API Mode: Disabled (placeholder mode)")
    
    # Collect all training examples
    all_examples = []
    per_file_outputs = {}  # Store per-file output paths
    start_time = time.time()
    
    logger.info("Starting dataset compilation...")
    
    for txt_file in sorted(txt_files):
        if shutdown_requested:
            print(f"\n⚠ Shutdown requested, stopping file processing...")
            logger.warning("Shutdown requested, stopping file processing")
            break
            
        category = Path(txt_file).stem  # Get filename without extension
        
        print(f"\n{'='*70}")
        print(f"Processing {category}.txt...")
        print(f"{'='*70}")
        logger.info(f"Processing {category}.txt")
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if use_api:
            # Prepare tasks
            tasks = []
            for idx, line in enumerate(lines):
                text_line = line.strip()
                if text_line:
                    instruction = f"以下內容請幫我去識別化並加上對照表。\n請先在 <thinking> 標籤中思考去識別化的步驟，然後再提供最終結果:\n\n{text_line}"
                    tasks.append((text_line, category, instruction, idx))
            
            logger.info(f"Prepared {len(tasks)} tasks for {category}.txt")
            
            print(f"  Processing {len(tasks)} examples with {max_workers} workers...")
            print(f"  Progress: ", end="", flush=True)
            
            # Process in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_task = {
                    executor.submit(create_training_example_with_api, text, cat, inst, idx): (text, cat, inst, idx)
                    for text, cat, inst, idx in tasks
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_task):
                    if shutdown_requested:
                        print(f"\n  ⚠ Cancelling remaining tasks...")
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    
                    try:
                        example = future.result()
                        if example:
                            file_examples.append(example)
                            
                            # Update progress
                            with progress_lock:
                                completed_count += 1
                                if completed_count % PROGRESS_UPDATE_INTERVAL == 0:
                                    progress = completed_count / len(tasks) * 100
                                    print(f"{completed_count}/{len(tasks)} ({progress:.1f}%) ", end="", flush=True)
                    except Exception as e:
                        print(f"\n  ⚠ Error processing example: {str(e)}")
            
            # Final progress
            print(f"{len(file_examples)}/{len(tasks)} (100%)")
            print(f"  ✓ Added {len(file_examples)} examples from {category}.txt")
            logger.success(f"Completed {category}.txt: {len(file_examples)} examples")
            
            # Write per-file output
            per_file_output = os.path.join(per_file_dir, f"{category}-thinking-{RUN_ID}.json")
            with open(per_file_output, 'w', encoding='utf-8') as f:
                json.dump(file_examples, f, ensure_ascii=False, indent=2)
            logger.info(f"Wrote {category} results to: {per_file_output}")
            per_file_outputs[category] = per_file_output
            
            all_examples.extend(file_examples)
            
        else:
            # Sequential processing mode (placeholder)
            line_count = 0
            file_examples = []
            for line in lines:
                example = create_training_example(line, category, use_api=False)
                if example:
                    file_examples.append(example)
                    line_count += 1
            
            print(f"  ✓ Added {line_count} examples from {category}.txt")
            logger.success(f"Completed {category}.txt: {line_count} examples (placeholder mode)")
            
            # Write per-file output
            per_file_output = os.path.join(per_file_dir, f"{category}-thinking-{RUN_ID}.json")
            with open(per_file_output, 'w', encoding='utf-8') as f:
                json.dump(file_examples, f, ensure_ascii=False, indent=2)
            logger.info(f"Wrote {category} results to: {per_file_output}")
            per_file_outputs[category] = per_file_output
            
            all_examples.extend(file_examples)
    
    elapsed_time = time.time() - start_time
    
    # Write merged output file
    print(f"\n{'='*70}")
    print(f"Writing {len(all_examples)} examples to {output_file}...")
    logger.info(f"Merging all results into: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_examples, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Dataset compiled successfully!")
    print(f"  Total examples: {len(all_examples)}")
    print(f"  Output file: {output_file}")
    print(f"  File size: {os.path.getsize(output_file) / 1024:.2f} KB")
    print(f"  Time elapsed: {elapsed_time:.1f} seconds")
    
    logger.success(f"Dataset compiled successfully: {len(all_examples)} examples")
    logger.info(f"Output file: {output_file} ({os.path.getsize(output_file) / 1024:.2f} KB)")
    logger.info(f"Time elapsed: {elapsed_time:.1f} seconds")
    
    if use_api and len(all_examples) > 0:
        print(f"  Avg time per example: {elapsed_time / len(all_examples):.2f} seconds")
        print(f"  Throughput: {len(all_examples) / elapsed_time:.2f} examples/second")
        logger.info(f"Avg time per example: {elapsed_time / len(all_examples):.2f} seconds")
    
    # Log per-file output summary
    print(f"\n{'='*70}")
    print(f"Per-file outputs in {per_file_dir}:")
    logger.info("Per-file output summary:")
    for category, filepath in per_file_outputs.items():
        file_size = os.path.getsize(filepath) / 1024
        print(f"  - {os.path.basename(filepath)} ({file_size:.2f} KB)")
        logger.info(f"  {category}: {os.path.basename(filepath)} ({file_size:.2f} KB)")




def main():

    import argparse
    
    # Declare global variable at the start
    global API_URL
    
    # Configure loguru logger
    log_file = f"compile_deid_{RUN_ID}.log"
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        level="DEBUG",
        rotation="100 MB",
        retention="30 days",
        compression="zip"
    )
    logger.info("="*70)
    logger.info("DEID Dataset Compiler Started")
    logger.info(f"RUN_ID: {RUN_ID}")
    logger.info("="*70)
            print(f"  ✓ Added {line_count} examples from {category}.txt")
    
    elapsed_time = time.time() - start_time
    
    # Write to output file
    print(f"\n{'='*70}")
    print(f"Writing {len(all_examples)} examples to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_examples, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Dataset compiled successfully!")
    print(f"  Total examples: {len(all_examples)}")
    print(f"  Output file: {output_file}")
    print(f"  File size: {os.path.getsize(output_file) / 1024:.2f} KB")
    print(f"  Time elapsed: {elapsed_time:.1f} seconds")
    if use_api and len(all_examples) > 0:
        print(f"  Avg time per example: {elapsed_time / len(all_examples):.2f} seconds")
        print(f"  Throughput: {len(all_examples) / elapsed_time:.2f} examples/second")


def main():

    import argparse
    
    # Declare global variable at the start
    global API_URL
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Compile DEID dataset from .txt files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate dataset with placeholder responses (fast)
  python compile_deid_dataset.py
  
  # Generate dataset using LLM API (slow but higher quality)
  python compile_deid_dataset.py --use-api
  
  # Specify custom API URL
  python compile_deid_dataset.py --use-api --api-url http://localhost:8000/v1/chat/completions
        """
    )
    
    parser.add_argument(
        '--use-api',
        action='store_true',
        help='Use LLM API to generate responses with thinking sections'
    )
    
    parser.add_argument(
        '--api-url',
        type=str,
        default=API_URL,
        help=f'API endpoint URL (default: {API_URL})'
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        default="/home/fychao/work/LLaMA-Factory/data/npu-csie/deid",
        help='Input directory containing .txt files'
    )
    
    parser.add_argument(
        '--output-name',
        type=str,
        help='Output filename (default: all_dataset_TIMESTAMP.json)'
    )
    
    parser.add_argument(
        '--max-workers',
    # Compile the dataset
    compile_dataset(input_dir, output_file, use_api=args.use_api, max_workers=args.max_workers)
    
    print("="*70)
    print("Done!")
    print("="*70)
    logger.info("="*70)
    logger.info("DEID Dataset Compiler Completed")
    logger.info("="*70)arse_args()
    
    # Update API URL if specified
    if args.api_url != API_URL:
        API_URL = args.api_url
    
    # Configuration
    input_dir = args.input_dir
    
    # Generate output filename with timestamp
    if args.output_name:
        output_filename = args.output_name
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "_api" if args.use_api else ""
        output_filename = f"all_dataset_{timestamp}{suffix}.json"
    
    output_file = os.path.join(input_dir, output_filename)
    
    print("=" * 70)
    print("DEID Dataset Compiler")
    print("=" * 70)
    print(f"Input directory: {input_dir}")
    print(f"Output file: {output_filename}")
    print("=" * 70)
    
    # Compile the dataset
    compile_dataset(input_dir, output_file, use_api=args.use_api, max_workers=args.max_workers)
    
    print("=" * 70)
    print("Done!")
    print("=" * 70)



if __name__ == "__main__":
    main()
