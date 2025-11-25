# HEIC Lead Image Text Extraction System

A Python-based system to extract structured contact/lead data from HEIC format images using Azure OpenAI vision models (GPT-4o).

## Features

- Converts HEIC images to JPEG format for Azure OpenAI compatibility
- Extracts comprehensive contact information using AI vision models
- Processes images in parallel for fast execution (5-15 minutes for 125 images)
- Uses structured outputs (Pydantic) for guaranteed valid JSON
- Exports to both JSON and CSV formats
- Includes error handling with automatic retry logic
- Provides detailed logging and progress tracking

## Requirements

- Python 3.9 or higher
- Azure OpenAI account with GPT-4o deployment
- HEIC images in the `lead_pics/` directory

## Installation

1. **Clone or navigate to the repository:**
   ```bash
   cd /Users/jq/Documents/Git/ai-extract-text-image
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Azure OpenAI credentials:
   ```bash
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   ```

## Usage

### Basic Execution

Simply run the main script:

```bash
python main.py
```

The system will:
1. Convert HEIC images to JPEG
2. Extract contact data using Azure OpenAI
3. Export results to JSON and CSV
4. Display progress and summary

### Output Files

All output files are saved to the `output/` directory:

- **`extracted_contacts.json`** - Complete extraction results with metadata
- **`extracted_contacts.csv`** - Flattened contact data for Excel
- **`extracted_contacts_summary.csv`** - Processing statistics
- **`failed_images_retry_list.txt`** - List of failed images for retry (if any failures)
- **`converted_images/`** - JPEG converted images
- **`extraction.log`** - Detailed processing logs (in project root)

### Data Schema

The system extracts the following fields from each image:

**Primary Contact:**
- full_name
- company_name
- job_title

**Contact Methods:**
- phone_number
- mobile_number
- email

**Address:**
- address
- city
- state
- zip_code
- country

**Additional:**
- last_contact_date (from middle of image)
- website
- notes
- confidence_score (high/medium/low)

## Configuration

You can adjust processing parameters in the `.env` file:

```bash
# Processing Configuration
MAX_CONCURRENT_REQUESTS=10    # Parallel processing limit
JPEG_QUALITY=90               # JPEG conversion quality (1-100)
MAX_IMAGE_WIDTH=2048          # Max width before resizing
```

## Troubleshooting

### "AZURE_OPENAI_API_KEY not set in environment"

Make sure you've:
1. Copied `.env.example` to `.env`
2. Added your actual Azure credentials to `.env`
3. Activated your virtual environment

### "No images were converted"

Check that:
1. HEIC images exist in the `lead_pics/` directory
2. Files have `.HEIC` or `.heic` extension
3. You have read permissions for the directory

### Import Errors

Ensure you've:
1. Activated the virtual environment: `source venv/bin/activate`
2. Installed all dependencies: `pip install -r requirements.txt`

### Rate Limit Errors (429)

The system includes automatic retry logic. If you still encounter rate limits:
1. Reduce `MAX_CONCURRENT_REQUESTS` in `.env` (try 5 instead of 10)
2. Check your Azure OpenAI quota limits in the portal

## Project Structure

```
ai-extract-text-image/
├── lead_pics/                    # Input HEIC images
├── output/                       # Generated outputs
│   ├── converted_images/         # JPEG conversions
│   ├── extracted_contacts.json   # Primary output
│   └── extracted_contacts.csv    # CSV export
├── src/                          # Source code
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── models.py                 # Pydantic data models
│   ├── image_converter.py        # HEIC → JPEG conversion
│   ├── batch_processor.py        # Azure OpenAI extraction
│   └── export.py                 # JSON/CSV export
├── main.py                       # Main execution script
├── requirements.txt              # Dependencies
├── .env.example                  # Environment template
├── .env                          # Your credentials (gitignored)
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## Cost Estimation

For 125 images using GPT-4o:
- **Estimated cost:** $1.50 - $2.50
- **Processing time:** 5-15 minutes

Actual costs depend on:
- Image size and complexity
- Azure OpenAI pricing tier
- Number of retries needed

## Advanced Usage

### Processing a Subset of Images

Move the images you want to process to `lead_pics/` and run the script.

### Reviewing Failed Extractions

Check the `errors` array in `extracted_contacts.json`:

```json
{
  "errors": [
    {
      "source_image": "IMG_7520.HEIC",
      "error": "Rate limit exceeded",
      "timestamp": "2025-11-25T14:25:30"
    }
  ]
}
```

### Re-running Failed Images

The system creates a retry list file when any images fail:

1. **Check the retry list:** `output/failed_images_retry_list.txt`
   - Lists all failed images by filename
   - Separates conversion failures from extraction failures
   - Includes error messages for each

2. **Review error details:** Check `extraction.log` for full error stack traces

3. **Retry failed images:**
   - Move failed images to a separate folder
   - Fix any issues (corrupted files, wrong format, etc.)
   - Move them back and re-run the script

**Example retry list:**
```
# Failed Image Processing - Retry List
# Generated: 2025-11-25T14:30:00

## Conversion Failures (HEIC → JPEG)
IMG_7520.HEIC	# Error: Unsupported image format

## Extraction Failures (Text Extraction)
IMG_7525.HEIC	# Error: Rate limit exceeded

# Total failures: 2
```

## Development

### Running Tests

```bash
pytest tests/
```

### Type Checking

```bash
mypy src/
```

### Code Structure

- **src/models.py** - Defines data schema using Pydantic
- **src/config.py** - Manages configuration and environment
- **src/image_converter.py** - Handles HEIC to JPEG conversion
- **src/batch_processor.py** - Core extraction logic with Azure OpenAI
- **src/export.py** - Export utilities for JSON and CSV
- **main.py** - Orchestrates the entire pipeline

## License

This project is for internal use. All rights reserved.

## Support

For issues or questions:
1. Check `extraction.log` for detailed error messages
2. Review the troubleshooting section above
3. Verify Azure credentials and quota limits
4. Ensure Python version is 3.9 or higher
