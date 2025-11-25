#!/usr/bin/env python3
"""
Main script to extract contact information from HEIC lead images
using Azure OpenAI GPT-4o with structured outputs.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from openai import AzureOpenAI

from src.config import Config
from src.image_converter import ImageConverter
from src.batch_processor import BatchProcessor
from src.export import export_to_json, export_to_csv, create_retry_list


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    try:
        # Initialize configuration
        logger.info("Initializing configuration...")
        config = Config()

        print("=" * 60)
        print("HEIC Lead Image Extraction System")
        print("=" * 60)
        print(f"Input directory: {config.input_dir}")
        print(f"Output directory: {config.output_dir}")
        print(f"Model: {config.model_name}")
        print("-" * 60)

        # Step 1: Convert HEIC images to JPEG
        print("\n[1/4] Converting HEIC images to JPEG...")
        logger.info("Starting HEIC to JPEG conversion")

        converter = ImageConverter(
            input_dir=config.input_dir,
            output_dir=config.converted_dir,
            quality=config.jpeg_quality,
            max_width=config.max_image_width
        )
        converted_images, failed_conversions = converter.convert_all()

        if not converted_images:
            print("Error: No images were converted. Please check:")
            print(f"  1. HEIC images exist in: {config.input_dir}")
            print("  2. Images have .HEIC or .heic extension")
            return 1

        print(f"✓ Converted {len(converted_images)} images")
        if failed_conversions:
            print(f"⚠ Failed to convert {len(failed_conversions)} images (see log)")

        # Step 2: Initialize Azure OpenAI client
        print("\n[2/4] Initializing Azure OpenAI client...")
        logger.info("Initializing Azure OpenAI client")

        client = AzureOpenAI(
            api_key=config.api_key,
            api_version=config.api_version,
            azure_endpoint=config.endpoint
        )
        print("✓ Client initialized successfully")

        # Step 3: Process images in parallel
        print(f"\n[3/4] Extracting contact data from {len(converted_images)} images...")
        print(f"Using {config.max_concurrent} concurrent requests")
        logger.info(f"Starting batch processing of {len(converted_images)} images")

        processor = BatchProcessor(
            client=client,
            model_name=config.model_name,
            max_concurrent=config.max_concurrent
        )

        # Run async batch processing
        results = asyncio.run(processor.process_batch(converted_images))

        # Analyze results
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']

        print(f"\n✓ Extraction complete:")
        print(f"  • Successful: {len(successful)}")
        print(f"  • Failed: {len(failed)}")

        if failed:
            print(f"\n⚠ Failed extractions:")
            for f in failed[:5]:  # Show first 5 failures
                print(f"  • {f['data'].get('source_image', 'unknown')}: {f['error']}")
            if len(failed) > 5:
                print(f"  ... and {len(failed) - 5} more (see extraction.log)")

        # Step 4: Export results
        print("\n[4/4] Exporting results...")
        logger.info("Exporting results to JSON and CSV")

        # Export to JSON
        json_path = config.output_dir / "extracted_contacts.json"
        export_to_json(results, json_path, config)
        print(f"  ✓ JSON exported to: {json_path}")

        # Export to CSV
        csv_path = config.output_dir / "extracted_contacts.csv"
        export_to_csv(results, csv_path, config)
        print(f"  ✓ CSV exported to: {csv_path}")
        print(f"  ✓ Summary exported to: {csv_path.parent / (csv_path.stem + '_summary.csv')}")

        # Create retry list if there are any failures
        all_failures = failed_conversions + [
            {"source_image": f['data'].get('source_image', 'unknown'), "error": f['error']}
            for f in failed
        ]
        if all_failures:
            retry_path = config.output_dir / "failed_images_retry_list.txt"
            create_retry_list(failed_conversions, failed, retry_path)
            print(f"  ✓ Retry list exported to: {retry_path}")

        # Final summary
        print(f"\n{'=' * 60}")
        print("✓ Extraction complete!")
        print(f"{'=' * 60}")
        print(f"Results saved to: {config.output_dir}")
        print(f"Log file: extraction.log")
        print(f"\nNext steps:")
        print(f"  1. Review {json_path.name} for complete data")
        print(f"  2. Open {csv_path.name} in Excel/Google Sheets")
        if all_failures:
            print(f"  3. Check failed_images_retry_list.txt for images to retry")
            print(f"  4. Review extraction.log for detailed error information")
        else:
            print(f"  3. Check extraction.log for processing details")

        # Return exit code based on results
        if len(failed) == 0:
            logger.info("All images processed successfully")
            return 0
        elif len(successful) > 0:
            logger.warning(f"{len(failed)} images failed to process")
            return 0  # Partial success
        else:
            logger.error("All images failed to process")
            return 1

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease ensure:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your Azure OpenAI credentials to .env")
        print("  3. Verify the credentials are correct")
        return 1

    except Exception as e:
        logger.exception("Unexpected error during execution")
        print(f"\n❌ Error: {e}")
        print("Check extraction.log for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
