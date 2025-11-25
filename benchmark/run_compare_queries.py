#!/usr/bin/env python3
import argparse
import json, requests
from pathlib import Path

parser = argparse.ArgumentParser(description='Run compare queries against running API')
parser.add_argument('--samples', '-s', default='benchmark/tmp_10_samples.json', help='path to the samples json file')
parser.add_argument('--out', '-o', default='benchmark/results/gpt_ikala_10_samples.json', help='output results file')
args = parser.parse_args()

p = Path(args.samples)
if not p.exists():
    print('samples file missing', p)
    raise SystemExit(1)
items = json.load(p.open('r', encoding='utf-8'))
results = []
for i, it in enumerate(items, 1):
    q = it.get('question') or it.get('instruction')
    # Try to locate the ground-truth label from the sample
    correct_raw = (it.get('answer') or it.get('correct') or it.get('output') or '')
    # extract single-letter answer from sample (A/B/C/D) if present
    import re
    m = re.search(r'答案是\s*([A-D])', correct_raw)
    if not m:
        m = re.search(r'([A-D])', correct_raw)
    correct_label = m.group(1) if m else ''
    choices = []
    for k in ['A', 'B', 'C', 'D']:
        if it.get(k):
            choices.append(f"{k}. {it[k]}")
    prompt = f"請回答以下選擇題，只需要回答選項字母（A、B、C或D）。\n\n問題：{q}\n\n選項：\n{chr(10).join(choices)}\n\n答案："
    payload = {"model": "default", "messages": [{"role": "user", "content": prompt}], "max_tokens": 16, "temperature": 0.1}
    try:
        r = requests.post('http://localhost:8000/v1/chat/completions', json=payload, timeout=30)
        r.raise_for_status()
        text = r.json()['choices'][0]['message']['content']
    except Exception as e:
        text = f'ERROR: {e}'
    print(f"{i}: subject={it.get('subject','')} correct={it.get('answer','')} response={text}")
    results.append({'index': i, 'subject': it.get('subject',''), 'question': q, 'correct': correct_label, 'response': text})

out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print('Saved results to', out)
