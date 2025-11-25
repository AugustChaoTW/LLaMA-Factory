#!/usr/bin/env python3
"""Compare two result files produced by run_compare_queries.py

Produces summary JSON and diffs JSON, and prints McNemar statistics.
"""
import argparse
import json
import re
from pathlib import Path
from math import sqrt


def parse_choice(text):
    if not text:
        return ''
    t = text.strip()
    # Find first letter A/B/C/D
    m = re.search(r"([A-D])", t)
    return m.group(1) if m else ''


def mcnemar(b, c):
    # continuity corrected chi-square for paired counts b (A correct only), c (B correct only)
    if b + c == 0:
        return {'b': b, 'c': c, 'chi2_cc': 0.0, 'p': 1.0}
    chi2 = ((abs(b - c) - 1) ** 2) / (b + c)
    # p-value for 1 degree of freedom: use math based survival function via exp for chi2-1 df
    # For df=1, the CDF relationship: p = 1 - erf(sqrt(chi2/2)) -- approximate via math.erfc
    try:
        import math
        p =  math.erfc(sqrt(chi2 / 2))
    except Exception:
        p = None
    return {'b': b, 'c': c, 'chi2_cc': chi2, 'p': p}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', '-s', required=True, help='original samples JSON file (for correct_text)')
    parser.add_argument('--ikala', required=True, help='ikala results file path')
    parser.add_argument('--base', required=True, help='base results file path')
    parser.add_argument('--out-prefix', default='benchmark/results/llama3', help='output prefix for summary/diffs')
    args = parser.parse_args()

    samples = json.load(open(args.samples, 'r', encoding='utf-8'))
    ikala = json.load(open(args.ikala, 'r', encoding='utf-8'))
    base = json.load(open(args.base, 'r', encoding='utf-8'))

    n = min(len(ikala), len(base), len(samples))
    rows = []
    ikala_correct = 0
    base_correct = 0
    both_correct = 0
    both_wrong = 0

    b_only = 0  # ikala correct, base wrong
    c_only = 0  # base correct, ikala wrong

    for i in range(n):
        s = samples[i]
        idx = i + 1
        correct_text = (s.get('answer') or s.get('correct') or s.get('output') or '').strip()
        # Try to find single-letter correct choice
        m = re.search(r'([A-D])', correct_text)
        correct_choice = m.group(1) if m else (ikala[i].get('correct') or base[i].get('correct') or '')

        ik_raw = ikala[i].get('response', '')
        bs_raw = base[i].get('response', '')
        ik_choice = parse_choice(ik_raw)
        bs_choice = parse_choice(bs_raw)

        ik_ok = (ik_choice != '' and correct_choice != '' and ik_choice == correct_choice)
        bs_ok = (bs_choice != '' and correct_choice != '' and bs_choice == correct_choice)

        if ik_ok:
            ikala_correct += 1
        if bs_ok:
            base_correct += 1
        if ik_ok and bs_ok:
            both_correct += 1
        if (not ik_ok) and (not bs_ok):
            both_wrong += 1
        if ik_ok and (not bs_ok):
            b_only += 1
        if bs_ok and (not ik_ok):
            c_only += 1

        rows.append({
            'index': idx,
            'correct_text': correct_text,
            'correct_choice': correct_choice,
            'ikala_choice': ik_choice,
            'ikala_ok': ik_ok,
            'base_choice': bs_choice,
            'base_ok': bs_ok,
            'ikala_raw': ik_raw,
            'base_raw': bs_raw,
        })

    summary = {
        'n': n,
        'ikala_correct': ikala_correct,
        'base_correct': base_correct,
        'ikala_acc': ikala_correct / n if n else 0.0,
        'base_acc': base_correct / n if n else 0.0,
        'both_correct': both_correct,
        'both_wrong': both_wrong,
        'n_diff': b_only + c_only,
    }

    stats = mcnemar(b_only, c_only)
    summary.update({'mcnemar': stats})

    out_prefix = args.out_prefix
    out_summary = Path(f"{out_prefix}_comparison_200_summary.json")
    out_diffs = Path(f"{out_prefix}_comparison_200_diffs.json")
    out_summary.parent.mkdir(parents=True, exist_ok=True)

    out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    out_diffs.write_text(json.dumps({'rows': rows}, ensure_ascii=False, indent=2), encoding='utf-8')

    print('Wrote', out_summary, out_diffs)
    print('Summary:', json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
