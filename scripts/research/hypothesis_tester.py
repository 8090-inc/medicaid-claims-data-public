"""Experimental hypothesis testing framework for research queries."""

import json
import logging
import os
import time

from config.project_config import ANALYSIS_DIR

logger = logging.getLogger('medicaid_fwa.research')


def test_hypothesis(con, hypothesis, analyzer_class=None):
    """Test a single hypothesis and return results.

    Args:
        con: DuckDB connection (read-only).
        hypothesis: dict with 'id', 'category', 'subcategory', 'sql_template', 'parameters'.
        analyzer_class: Optional analyzer class to use. If None, executes SQL directly.

    Returns:
        dict with 'hypothesis_id', 'findings', 'elapsed_seconds', 'status'.
    """
    t0 = time.time()
    h_id = hypothesis.get('id', 'unknown')

    if analyzer_class:
        try:
            analyzer = analyzer_class()
            findings = analyzer.execute(hypothesis, con)
            status = 'success'
        except Exception as e:
            logger.error(f'Hypothesis {h_id} failed: {e}')
            findings = []
            status = f'error: {e}'
    else:
        sql = hypothesis.get('sql_template', '')
        params = hypothesis.get('parameters', {})
        if sql:
            try:
                rows = con.execute(sql).fetchall()
                findings = [{'row': list(r)} for r in rows[:1000]]
                status = 'success'
            except Exception as e:
                logger.error(f'SQL execution failed for {h_id}: {e}')
                findings = []
                status = f'error: {e}'
        else:
            findings = []
            status = 'no_sql_template'

    elapsed = time.time() - t0
    logger.info(f'Hypothesis {h_id}: {len(findings)} findings in {elapsed:.3f}s [{status}]')

    return {
        'hypothesis_id': h_id,
        'findings': findings,
        'elapsed_seconds': round(elapsed, 3),
        'status': status,
    }


def batch_test_hypotheses(con, hypotheses, analyzer_map=None, max_workers=1):
    """Test a batch of hypotheses sequentially.

    Args:
        con: DuckDB connection (read-only).
        hypotheses: List of hypothesis dicts.
        analyzer_map: dict mapping category -> analyzer class.
        max_workers: Reserved for future parallel execution.

    Returns:
        list of result dicts from test_hypothesis.
    """
    results = []
    analyzer_map = analyzer_map or {}

    for h in hypotheses:
        category = h.get('category', '')
        analyzer_class = analyzer_map.get(category)
        result = test_hypothesis(con, h, analyzer_class)
        results.append(result)

    successes = sum(1 for r in results if r['status'] == 'success')
    logger.info(f'Batch test: {successes}/{len(results)} hypotheses succeeded')
    return results


def save_test_results(results, filename='hypothesis_test_results.json'):
    """Save hypothesis test results to JSON.

    Args:
        results: List of result dicts.
        filename: Output filename.

    Returns:
        Path to saved file.
    """
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    path = os.path.join(ANALYSIS_DIR, filename)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f'Saved {len(results)} test results to {path}')
    return path
