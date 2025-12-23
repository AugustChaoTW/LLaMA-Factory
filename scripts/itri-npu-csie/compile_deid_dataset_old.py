#!/usr/bin/env python3
"""
DEID Dataset Compiler with Enhanced Logging and Per-File Output

Features:
- Loguru logging for detailed tracking
- Per-file JSON outputs with RUN_ID
- Final merged output
- API mode with parallel processing
- Graceful shutdown handling
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
MAX_WORKERS = 32
PROGRESS_UPDATE_INTERVAL = 5

# Global state
shutdown_requested = False
progress_lock = Lock()
completed_count = 0

# Generate unique RUN_ID
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print("\n\n⚠ Interrupt received! Finishing current requests...")
    logger.warning("Interrupt signal received, initiating graceful shutdown")
    shutdown_requested = True
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(1))


def call_llm_api(prompt, retry_count=0, record_id=None):
    """Call the LLM API to generate a response."""
    logger.debug(f"[{record_id}] API call attempt {retry_count + 1}/{API_RETRY_ATTEMPTS}")
    
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
            logger.success(f"[{record_id}] API success, {len(content)} chars")
            return content
        else:
            logger.warning(f"[{record_id}] API error {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning(f"[{record_id}] Timeout attempt {retry_count + 1}")
        if retry_count < API_RETRY_ATTEMPTS - 1:
            time.sleep(API_RETRY_DELAY)
            return call_llm_api(prompt, retry_count + 1, record_id)
        return None
        
    except Exception as e:
        logger.error(f"[{record_id}] Exception: {str(e)}")
        return None


def create_example_with_api(text_line, category, instruction, record_idx):
    """Create a training example using API."""
    global shutdown_requested
    
    record_id = f"{category}_{record_idx:04d}"
    logger.info(f"[{record_id}] Processing: {text_line[:50]}...")
    
    if shutdown_requested:
        logger.warning(f"[{record_id}] Skipped (shutdown)")
        return None
    
    # Call API
    assistant_response = call_llm_api(instruction, record_id=record_id)
    
    if not assistant_response:
        # Fallback
        assistant_response = f"[此為來自 {category}.txt 的原始資料，需要進行去識別化處理]\n\n{text_line}"
        logger.warning(f"[{record_id}] Using fallback")
    
    example = {
        "messages": [
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": assistant_response}
        ]
    }
    
    logger.debug(f"[{record_id}] Example created")
    return example


def create_example_placeholder(text_line, category):
    """Create a placeholder training example (no API)."""
    if not text_line.strip():
        return None
    
    instruction = f"以下內容請幫我去識別化並加上對照表。\n請先在 <thinking> 標籤中思考去識別化的步驟，然後再提供最終結果:\n\n{text_line}"
    assistant_response = f"[此為來自 {category}.txt 的原始資料，需要進行去識別化處理]\n\n{text_line}"
    
    return {
        "messages": [
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": assistant_response}
        ]
    }


def process_file(txt_file, per_file_dir, use_api, max_workers):
    """Process a single .txt file."""
    global shutdown_requested, completed_count
    
    category = Path(txt_file).stem
    logger.info(f"Processing {category}.txt")
    print(f"\n{'='*70}")
    print(f"Processing {category}.txt...")
    print(f"{'='*70}")
    
    with open(txt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    file_examples = []
    
    if use_api:
        # API mode with parallel processing
        tasks = []
        for idx, line in enumerate(lines):
            text_line = line.strip()
            if text_line:
                instruction = f"以下內容請幫我去識別化並加上對照表。\n請先在 <thinking> 標籤中思考去識別化的步驟，然後再提供最終結果:\n\n{text_line}"
                tasks.append((text_line, category, instruction, idx))
        
        logger.info(f"Prepared {len(tasks)} tasks for {category}.txt")
        print(f"  Processing {len(tasks)} examples with {max_workers} workers...")
        print(f"  Progress: ", end="", flush=True)
        
        # Parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(create_example_with_api, text, cat, inst, idx): idx
                for text, cat, inst, idx in tasks
            }
            
            for future in as_completed(future_to_task):
                if shutdown_requested:
                    print(f"\n  ⚠ Cancelling...")
                    logger.warning("Cancelling remaining tasks")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                try:
                    example = future.result()
                    if example:
                        file_examples.append(example)
                        
                        with progress_lock:
                            completed_count += 1
                            if completed_count % PROGRESS_UPDATE_INTERVAL == 0:
                                progress = len(file_examples) / len(tasks) * 100
                                print(f"{len(file_examples)}/{len(tasks)} ({progress:.1f}%) ", end="", flush=True)
                except Exception as e:
                    logger.error(f"Error processing example: {str(e)}")
        
        print(f"{len(file_examples)}/{len(tasks)} (100%)")
    
    else:
        # Placeholder mode (sequential)
        for line in lines:
            example = create_example_placeholder(line.strip(), category)
            if example:
                file_examples.append(example)
    
    print(f"  ✓ Added {len(file_examples)} examples from {category}.txt")
    logger.success(f"Completed {category}.txt: {len(file_examples)} examples")
    
    # Write per-file output
    per_file_output = os.path.join(per_file_dir, f"{category}-thinking-{RUN_ID}.json")
    with open(per_file_output, 'w', encoding='utf-8') as f:
        json.dump(file_examples, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Wrote {category} to: {per_file_output}")
    
    return category, per_file_output, file_examples


def compile_dataset(input_dir, output_file, use_api=False, max_workers=MAX_WORKERS):
    """Compile all *.txt files into dataset with per-file outputs."""
    global shutdown_requested, completed_count
    
    # Create per-file output directory
    per_file_dir = os.path.join(input_dir, "thinking-gpt120b")
    os.makedirs(per_file_dir, exist_ok=True)
    logger.info(f"Output directory: {per_file_dir}")
    logger.info(f"RUN_ID: {RUN_ID}")
    
    # Find all .txt files
    txt_files = sorted(glob.glob(os.path.join(input_dir, "*.txt")))
    
    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        logger.error(f"No .txt files found in {input_dir}")
        return
    
    print(f"Found {len(txt_files)} .txt files:")
    logger.info(f"Found {len(txt_files)} .txt files")
    for txt_file in txt_files:
        print(f"  - {os.path.basename(txt_file)}")
        logger.info(f"  - {os.path.basename(txt_file)}")
    
    if use_api:
        print(f"\n⚡ API Mode: Enabled")
        print(f"   URL: {API_URL}")
        print(f"   Workers: {max_workers}")
        logger.info(f"API Mode: ON, Workers: {max_workers}")
        
        # Test API
        print(f"\nTesting API...")
        test_response = call_llm_api("Hello", record_id="test")
        if test_response:
            print(f"✓ API OK")
            logger.success("API test passed")
        else:
            print(f"✗ API failed, using placeholder")
            logger.error("API test failed, falling back")
            use_api = False
    else:
        print(f"\n📝 Placeholder Mode")
        logger.info("Placeholder mode")
    
    # Process all files
    all_examples = []
    per_file_outputs = {}
    start_time = time.time()
    
    logger.info("Starting compilation...")
    
    for txt_file in txt_files:
        if shutdown_requested:
            print(f"\n⚠ Shutdown, stopping...")
            logger.warning("Shutdown, stopping")
            break
        
        category, filepath, examples = process_file(txt_file, per_file_dir, use_api, max_workers)
        per_file_outputs[category] = filepath
        all_examples.extend(examples)
    
    elapsed_time = time.time() - start_time
    
    # Write merged output
    print(f"\n{'='*70}")
    print(f"Writing {len(all_examples)} examples to {output_file}...")
    logger.info(f"Merging to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_examples, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(output_file) / 1024
    
    print(f"✓ Dataset compiled!")
    print(f"  Total: {len(all_examples)} examples")
    print(f"  Output: {output_file}")
    print(f"  Size: {file_size:.2f} KB")
    print(f"  Time: {elapsed_time:.1f}s")
    
    logger.success(f"Compiled: {len(all_examples)} examples")
    logger.info(f"Output: {output_file} ({file_size:.2f} KB)")
    logger.info(f"Time: {elapsed_time:.1f}s")
    
    if use_api and len(all_examples) > 0:
        avg_time = elapsed_time / len(all_examples)
        throughput = len(all_examples) / elapsed_time
        print(f"  Avg/example: {avg_time:.2f}s")
        print(f"  Throughput: {throughput:.2f}/s")
        logger.info(f"Avg: {avg_time:.2f}s, Throughput: {throughput:.2f}/s")
    
    # Per-file summary
    print(f"\n{'='*70}")
    print(f"Per-file outputs in {per_file_dir}:")
    logger.info("Per-file summary:")
    for category, filepath in per_file_outputs.items():
        size = os.path.getsize(filepath) / 1024
        print(f"  - {os.path.basename(filepath)} ({size:.2f} KB)")
        logger.info(f"  {category}: {os.path.basename(filepath)} ({size:.2f} KB)")


def main():
    import argparse
    
    global API_URL
    
    # Setup loguru
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
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Compile DEID dataset with per-file outputs and logging"
    )
    
    parser.add_argument('--use-api', action='store_true',
                        help='Use LLM API for responses')
    parser.add_argument('--api-url', type=str, default=API_URL,
                        help=f'API URL (default: {API_URL})')
    parser.add_argument('--input-dir', type=str,
                        default="/home/fychao/work/LLaMA-Factory/data/npu-csie/deid",
                        help='Input directory')
    parser.add_argument('--output-name', type=str,
                        help='Output filename')
    parser.add_argument('--max-workers', type=int, default=MAX_WORKERS,
                        help=f'Max workers (default: {MAX_WORKERS})')
    
    args = parser.parse_args()
    
    # Update API URL
    if args.api_url != API_URL:
        API_URL = args.api_url
        logger.info(f"Using custom API URL: {API_URL}")
    
    # Generate output filename
    if args.output_name:
        output_filename = args.output_name
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "_api" if args.use_api else ""
        output_filename = f"all_dataset_{timestamp}{suffix}.json"
    
    output_file = os.path.join(args.input_dir, output_filename)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("="*70)
    print("DEID Dataset Compiler")
    print("="*70)
    print(f"Input: {args.input_dir}")
    print(f"Output: {output_filename}")
    print(f"RUN_ID: {RUN_ID}")
    print(f"Log: {log_file}")
    print("="*70)
    
    logger.info(f"Input: {args.input_dir}")
    logger.info(f"Output: {output_filename}")
    
    # Compile
    compile_dataset(args.input_dir, output_file, 
                    use_api=args.use_api, 
                    max_workers=args.max_workers)
    
    print("="*70)
    print("Done!")
    print("="*70)
    
    logger.info("="*70)
    logger.info("DEID Dataset Compiler Completed")
    logger.info("="*70)


if __name__ == "__main__":
    main()
