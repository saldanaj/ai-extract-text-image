"""Export utilities for JSON and CSV output"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict


def create_retry_list(
    failed_conversions: List[Dict],
    failed_extractions: List[Dict],
    output_path: Path
) -> None:
    """Create a retry list file with all failed images

    Args:
        failed_conversions: List of conversion failures
        failed_extractions: List of extraction failures
        output_path: Path to retry list file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Failed Image Processing - Retry List\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n\n")

        if failed_conversions:
            f.write("## Conversion Failures (HEIC → JPEG)\n")
            for item in failed_conversions:
                f.write(f"{item['filename']}\t# Error: {item['error']}\n")
            f.write("\n")

        if failed_extractions:
            f.write("## Extraction Failures (Text Extraction)\n")
            for item in failed_extractions:
                f.write(f"{item['source_image']}\t# Error: {item['error']}\n")
            f.write("\n")

        total_failed = len(failed_conversions) + len(failed_extractions)
        f.write(f"# Total failures: {total_failed}\n")


def export_to_json(results: List[Dict], output_path: Path, config) -> None:
    """Export results to structured JSON

    Args:
        results: List of extraction result dictionaries
        output_path: Path to output JSON file
        config: Configuration object with metadata
    """
    # Separate successful and failed results
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']

    # Build output structure
    output = {
        "metadata": {
            "total_images": len(results),
            "processed": len(successful) + len(failed),
            "successful": len(successful),
            "failed": len(failed),
            "processing_date": datetime.now().isoformat(),
            "model_used": config.model_name,
            "api_version": config.api_version
        },
        "contacts": [r['data'] for r in successful],
        "errors": [
            {
                "source_image": r['data'].get('source_image', 'unknown'),
                "error": r['error'],
                "timestamp": datetime.now().isoformat()
            }
            for r in failed
        ]
    }

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def export_to_csv(results: List[Dict], output_path: Path, config) -> None:
    """Export results to CSV format

    Args:
        results: List of extraction result dictionaries
        output_path: Path to output CSV file
        config: Configuration object with metadata
    """
    # Extract successful contacts
    successful = [r['data'] for r in results if r['status'] == 'success']

    if not successful:
        # Create empty CSV with headers
        df = pd.DataFrame(columns=[
            'source_image', 'full_name', 'company_name', 'job_title',
            'email', 'phone_number', 'mobile_number',
            'address', 'city', 'state', 'zip_code', 'country',
            'last_contact_date', 'website', 'notes', 'confidence_score'
        ])
    else:
        # Create DataFrame
        df = pd.DataFrame(successful)

        # Reorder columns for readability
        column_order = [
            'source_image', 'full_name', 'company_name', 'job_title',
            'email', 'phone_number', 'mobile_number',
            'address', 'city', 'state', 'zip_code', 'country',
            'last_contact_date', 'website', 'notes', 'confidence_score'
        ]

        # Only include columns that exist
        column_order = [col for col in column_order if col in df.columns]
        df = df[column_order]

    # Export to CSV
    df.to_csv(output_path, index=False, encoding='utf-8')

    # Also create summary CSV
    summary_data = {
        "total_images": len(results),
        "successful": len([r for r in results if r['status'] == 'success']),
        "failed": len([r for r in results if r['status'] == 'failed']),
        "processing_date": datetime.now().isoformat(),
        "model_used": config.model_name
    }

    summary_df = pd.DataFrame([summary_data])
    summary_path = output_path.parent / f"{output_path.stem}_summary.csv"
    summary_df.to_csv(summary_path, index=False)
