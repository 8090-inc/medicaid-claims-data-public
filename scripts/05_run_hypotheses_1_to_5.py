#!/usr/bin/env python3
"""Milestone 5: Parallel hypothesis execution for Categories 1-5.

Uses ProcessPoolExecutor with max_workers=10 to run hypothesis batches
in parallel. Each worker opens a read-only DuckDB connection, loads
hypotheses from a batch file, routes to the appropriate analyzer,
and writes findings to output/findings/batch_NN.json.

After all workers complete, merges results into
output/findings/categories_1_to_5.json.
"""

import json
import os
import sys
import time
import glob
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
HYPOTHESES_DIR = os.path.join(PROJECT_ROOT, 'output', 'hypotheses')
FINDINGS_DIR = os.path.join(PROJECT_ROOT, 'output', 'findings')

# Ensure scripts directory is on the path for imports
sys.path.insert(0, SCRIPTS_DIR)

from utils.db_utils import get_connection
from analyzers.statistical_analyzer import StatisticalAnalyzer
from analyzers.temporal_analyzer import TemporalAnalyzer
from analyzers.peer_analyzer import PeerAnalyzer
from analyzers.network_analyzer import NetworkAnalyzer
from analyzers.concentration_analyzer import ConcentrationAnalyzer


# Category to analyzer class mapping
ANALYZER_MAP = {
    '1': StatisticalAnalyzer,
    '2': TemporalAnalyzer,
    '3': PeerAnalyzer,
    '4': NetworkAnalyzer,
    '5': ConcentrationAnalyzer,
}


def get_analyzer(category):
    """Instantiate the appropriate analyzer for a category string.

    Args:
        category: string like '1', '2', '3', '4', '5' or with prefix like 'Category 1'

    Returns:
        Analyzer instance or None
    """
    # Normalize category to just the number
    cat_num = str(category).strip()
    for prefix in ['Category ', 'Cat ', 'category ', 'cat ']:
        if cat_num.startswith(prefix):
            cat_num = cat_num[len(prefix):]
            break
    cat_num = cat_num.strip()

    analyzer_cls = ANALYZER_MAP.get(cat_num)
    if analyzer_cls is None:
        return None
    return analyzer_cls()


def run_single_hypothesis(hypothesis, con):
    """Execute a single hypothesis and return findings.

    Args:
        hypothesis: dict with at minimum 'id', 'category', 'subcategory'
        con: duckdb connection (read-only)

    Returns:
        list of finding dicts
    """
    hyp_id = hypothesis.get('id', 'unknown')
    category = hypothesis.get('category', '')

    analyzer = get_analyzer(category)
    if analyzer is None:
        print(f"  [SKIP] Hypothesis {hyp_id}: no analyzer for category '{category}'")
        return []

    try:
        findings = analyzer.execute(hypothesis, con)
        print(f"  [OK] Hypothesis {hyp_id}: {len(findings)} findings")
        return findings
    except Exception as e:
        print(f"  [ERROR] Hypothesis {hyp_id}: {e}")
        traceback.print_exc()
        return []


def process_batch(batch_path):
    """Worker function: process a batch of hypotheses.

    Opens a read-only DuckDB connection, loads hypotheses from the batch
    file, routes each to the appropriate analyzer, catches exceptions
    per hypothesis (logs and continues), and writes findings to
    output/findings/batch_NN.json.

    Args:
        batch_path: path to a JSON file containing a list of hypothesis dicts

    Returns:
        dict with 'batch_file', 'num_hypotheses', 'num_findings',
        'findings_path', 'errors', 'elapsed_seconds'
    """
    t0 = time.time()
    batch_name = os.path.splitext(os.path.basename(batch_path))[0]
    findings_path = os.path.join(FINDINGS_DIR, f"{batch_name}.json")
    result = {
        'batch_file': batch_path,
        'batch_name': batch_name,
        'num_hypotheses': 0,
        'num_findings': 0,
        'findings_path': findings_path,
        'errors': [],
        'elapsed_seconds': 0,
    }

    # Load hypotheses
    try:
        with open(batch_path, 'r') as f:
            hypotheses = json.load(f)
    except Exception as e:
        result['errors'].append(f"Failed to load batch file: {e}")
        return result

    if not isinstance(hypotheses, list):
        # Handle case where batch file is a dict with a 'hypotheses' key
        if isinstance(hypotheses, dict) and 'hypotheses' in hypotheses:
            hypotheses = hypotheses['hypotheses']
        else:
            result['errors'].append("Batch file does not contain a list of hypotheses")
            return result

    result['num_hypotheses'] = len(hypotheses)
    print(f"\n=== Processing batch {batch_name}: {len(hypotheses)} hypotheses ===")

    # Open read-only DuckDB connection
    try:
        con = get_connection(read_only=True)
    except Exception as e:
        result['errors'].append(f"Failed to connect to DuckDB: {e}")
        return result

    all_findings = []

    for hypothesis in hypotheses:
        hyp_id = hypothesis.get('id', 'unknown')
        try:
            findings = run_single_hypothesis(hypothesis, con)
            for finding in findings:
                finding['batch'] = batch_name
            all_findings.extend(findings)
        except Exception as e:
            error_msg = f"Hypothesis {hyp_id}: {e}"
            result['errors'].append(error_msg)
            print(f"  [FATAL] {error_msg}")
            traceback.print_exc()
            continue

    # Close connection
    try:
        con.close()
    except Exception:
        pass

    # Write findings
    result['num_findings'] = len(all_findings)
    try:
        os.makedirs(FINDINGS_DIR, exist_ok=True)
        with open(findings_path, 'w') as f:
            json.dump(all_findings, f, indent=2, default=str)
        print(f"  Wrote {len(all_findings)} findings to {findings_path}")
    except Exception as e:
        result['errors'].append(f"Failed to write findings: {e}")

    result['elapsed_seconds'] = round(time.time() - t0, 1)
    return result


def discover_batch_files():
    """Find all hypothesis batch files in the hypotheses directory.

    Looks for files matching patterns:
      - batch_*.json
      - hypotheses_*.json
      - categories_*.json

    Returns:
        sorted list of file paths
    """
    batch_files = sorted(glob.glob(os.path.join(HYPOTHESES_DIR, 'batch_*.json')))
    if batch_files:
        return batch_files

    files = set()
    patterns = [
        os.path.join(HYPOTHESES_DIR, 'hypotheses_*.json'),
        os.path.join(HYPOTHESES_DIR, 'categories_*.json'),
    ]
    for pattern in patterns:
        files.update(glob.glob(pattern))

    # Prefer the testable monolith when present
    for monolithic_name in ('all_hypotheses_testable.json', 'all_hypotheses.json'):
        monolithic = os.path.join(HYPOTHESES_DIR, monolithic_name)
        if os.path.exists(monolithic):
            files.add(monolithic)
            break

    return sorted(files)


def split_into_batches(hypotheses, batch_size=50):
    """Split a list of hypotheses into batch files for parallel processing.

    Args:
        hypotheses: list of hypothesis dicts
        batch_size: number of hypotheses per batch

    Returns:
        list of batch file paths created
    """
    os.makedirs(HYPOTHESES_DIR, exist_ok=True)
    batch_files = []
    for i in range(0, len(hypotheses), batch_size):
        batch_num = i // batch_size
        batch = hypotheses[i:i + batch_size]
        batch_path = os.path.join(HYPOTHESES_DIR, f"batch_{batch_num:02d}.json")
        with open(batch_path, 'w') as f:
            json.dump(batch, f, indent=2, default=str)
        batch_files.append(batch_path)
        print(f"  Created {batch_path} with {len(batch)} hypotheses")
    return batch_files


def merge_findings(batch_results):
    """Merge all batch finding files into a single combined output.

    Args:
        batch_results: list of result dicts from process_batch

    Returns:
        path to merged output file
    """
    merged = []
    for result in batch_results:
        findings_path = result.get('findings_path', '')
        if os.path.exists(findings_path):
            try:
                with open(findings_path, 'r') as f:
                    batch_findings = json.load(f)
                merged.extend(batch_findings)
            except Exception as e:
                print(f"  Warning: could not read {findings_path}: {e}")

    # Sort by total_impact descending
    merged.sort(key=lambda x: x.get('total_impact', 0), reverse=True)

    merged_path = os.path.join(FINDINGS_DIR, 'categories_1_to_5.json')
    os.makedirs(FINDINGS_DIR, exist_ok=True)
    with open(merged_path, 'w') as f:
        json.dump(merged, f, indent=2, default=str)

    print(f"\nMerged {len(merged)} findings into {merged_path}")
    return merged_path


def generate_default_hypotheses():
    """Generate a default set of hypotheses covering categories 1-5
    when no batch files exist yet.

    Returns:
        list of hypothesis dicts
    """
    hypotheses = []
    hyp_id = 0

    # --- Category 1: Statistical Outlier Detection ---
    for sub in ['1A', '1B', '1C']:
        hyp_id += 1
        hypotheses.append({
            'id': f"H{hyp_id:04d}",
            'category': '1',
            'subcategory': sub,
            'description': f"Statistical outlier detection ({sub})",
            'parameters': {},
        })

    # 1D: IQR on various metrics
    for metric in ['total_paid', 'avg_paid_per_claim', 'total_claims']:
        hyp_id += 1
        hypotheses.append({
            'id': f"H{hyp_id:04d}",
            'category': '1',
            'subcategory': '1D',
            'description': f"IQR outlier on {metric}",
            'parameters': {'metric': metric},
        })

    # 1E: GEV on key categories
    for category in ['Behavioral Health', 'Home Health', 'Pharmacy', 'DME', 'Therapy']:
        hyp_id += 1
        hypotheses.append({
            'id': f"H{hyp_id:04d}",
            'category': '1',
            'subcategory': '1E',
            'description': f"GEV extreme value for {category}",
            'parameters': {'category': category, 'metric': 'paid_per_claim'},
        })

    # 1F: Benford's Law
    hyp_id += 1
    hypotheses.append({
        'id': f"H{hyp_id:04d}",
        'category': '1',
        'subcategory': '1F',
        'description': "Benford's Law and round-number detection",
        'parameters': {},
    })

    # --- Category 2: Temporal Analysis ---
    for sub in ['2A', '2B', '2C', '2D', '2E', '2F', '2G', '2H']:
        hyp_id += 1
        hypotheses.append({
            'id': f"H{hyp_id:04d}",
            'category': '2',
            'subcategory': sub,
            'description': f"Temporal pattern ({sub})",
            'parameters': {},
        })

    # --- Category 3: Peer Comparison ---
    for sub in ['3A', '3B', '3C', '3D', '3E', '3F']:
        hyp_id += 1
        hypotheses.append({
            'id': f"H{hyp_id:04d}",
            'category': '3',
            'subcategory': sub,
            'description': f"Peer comparison ({sub})",
            'parameters': {},
        })

    # --- Category 4: Network Analysis ---
    for sub in ['4A', '4B', '4C', '4D', '4E', '4F', '4G']:
        hyp_id += 1
        hypotheses.append({
            'id': f"H{hyp_id:04d}",
            'category': '4',
            'subcategory': sub,
            'description': f"Network analysis ({sub})",
            'parameters': {},
        })

    # --- Category 5: Concentration Analysis ---
    for sub in ['5A', '5B', '5C', '5D', '5E']:
        hyp_id += 1
        hypotheses.append({
            'id': f"H{hyp_id:04d}",
            'category': '5',
            'subcategory': sub,
            'description': f"Concentration analysis ({sub})",
            'parameters': {},
        })

    return hypotheses


def main():
    """Main entry point: discover or generate hypothesis batches,
    run them in parallel, and merge the results.
    """
    t0 = time.time()
    max_workers = 10

    os.makedirs(HYPOTHESES_DIR, exist_ok=True)
    os.makedirs(FINDINGS_DIR, exist_ok=True)

    # Step 1: Discover existing batch files
    batch_files = discover_batch_files()

    if not batch_files:
        print("No hypothesis batch files found. Generating default hypotheses ...")
        hypotheses = generate_default_hypotheses()
        print(f"Generated {len(hypotheses)} default hypotheses")
        batch_files = split_into_batches(hypotheses, batch_size=10)

    print(f"\nFound {len(batch_files)} batch files to process")
    for bf in batch_files:
        print(f"  {bf}")

    # Step 2: Run batches in parallel
    print(f"\nStarting parallel execution with max_workers={max_workers} ...")
    batch_results = []

    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {
                executor.submit(process_batch, bf): bf
                for bf in batch_files
            }

            for future in as_completed(future_to_batch):
                batch_path = future_to_batch[future]
                try:
                    result = future.result()
                    batch_results.append(result)
                    print(
                        f"\n  Batch {result['batch_name']}: "
                        f"{result['num_findings']} findings from "
                        f"{result['num_hypotheses']} hypotheses "
                        f"in {result['elapsed_seconds']}s"
                    )
                    if result['errors']:
                        for err in result['errors']:
                            print(f"    ERROR: {err}")
                except Exception as e:
                    print(f"\n  FATAL: Batch {batch_path} failed: {e}")
                    traceback.print_exc()
                    batch_results.append({
                        'batch_file': batch_path,
                        'batch_name': os.path.splitext(os.path.basename(batch_path))[0],
                        'num_hypotheses': 0,
                        'num_findings': 0,
                        'findings_path': '',
                        'errors': [str(e)],
                        'elapsed_seconds': 0,
                    })
    except PermissionError as e:
        print(f"\nParallel execution unavailable ({e}); falling back to sequential.")
        max_workers = 1
        for bf in batch_files:
            result = process_batch(bf)
            batch_results.append(result)
            print(
                f"\n  Batch {result['batch_name']}: "
                f"{result['num_findings']} findings from "
                f"{result['num_hypotheses']} hypotheses "
                f"in {result['elapsed_seconds']}s"
            )
            if result['errors']:
                for err in result['errors']:
                    print(f"    ERROR: {err}")

    # Step 3: Merge all findings
    print("\n=== Merging findings ===")
    merged_path = merge_findings(batch_results)

    # Step 4: Summary
    total_hypotheses = sum(r['num_hypotheses'] for r in batch_results)
    total_findings = sum(r['num_findings'] for r in batch_results)
    total_errors = sum(len(r['errors']) for r in batch_results)
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"EXECUTION SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Batches processed:   {len(batch_results)}")
    print(f"  Total hypotheses:    {total_hypotheses}")
    print(f"  Total findings:      {total_findings}")
    print(f"  Total errors:        {total_errors}")
    print(f"  Workers:             {max_workers}")
    print(f"  Total time:          {elapsed:.1f}s")
    print(f"  Output:              {merged_path}")
    print(f"{'=' * 60}")

    # Write execution summary
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_hypotheses': total_hypotheses,
        'total_findings': total_findings,
        'total_errors': total_errors,
        'max_workers': max_workers,
        'elapsed_seconds': round(elapsed, 1),
        'merged_output': merged_path,
        'batch_results': [
            {
                'batch_name': r['batch_name'],
                'num_hypotheses': r['num_hypotheses'],
                'num_findings': r['num_findings'],
                'errors': r['errors'],
                'elapsed_seconds': r['elapsed_seconds'],
            }
            for r in batch_results
        ],
    }
    summary_path = os.path.join(FINDINGS_DIR, 'execution_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nExecution summary written to {summary_path}")

    if total_errors > 0:
        print(f"\nWARNING: {total_errors} errors occurred. Check batch results for details.")

    print(f"\nMilestone 5 complete.")


if __name__ == '__main__':
    main()
