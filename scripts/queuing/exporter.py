"""Queue export utilities — CSV, JSON formats."""

import csv
import json
import logging
import os

from config.project_config import ANALYSIS_DIR

logger = logging.getLogger('medicaid_fwa.queuing')


def export_queue_csv(queue_data, filename, output_dir=None):
    """Export a queue to CSV format.

    Args:
        queue_data: List of dicts to export.
        filename: Output filename.
        output_dir: Output directory.

    Returns:
        Path to exported file.
    """
    output_dir = output_dir or ANALYSIS_DIR
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)

    if not queue_data:
        logger.warning(f'No data to export for {filename}')
        return path

    keys = queue_data[0].keys()
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(queue_data)

    logger.info(f'Exported {len(queue_data)} rows to {path}')
    return path


def export_queue_json(queue_data, filename, output_dir=None):
    """Export a queue to JSON format.

    Args:
        queue_data: Data to export.
        filename: Output filename.
        output_dir: Output directory.

    Returns:
        Path to exported file.
    """
    output_dir = output_dir or ANALYSIS_DIR
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)

    with open(path, 'w') as f:
        json.dump(queue_data, f, indent=2)

    logger.info(f'Exported JSON to {path}')
    return path
