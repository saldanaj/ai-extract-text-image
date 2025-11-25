# HEIC Lead Image Text Extraction System - Implementation Plan

## Overview
Build a Python-based system to extract structured contact/lead data from 125 HEIC format images using Azure OpenAI vision models, outputting to JSON and CSV formats.

## Architecture Summary

**Tech Stack:**
- Python 3.9+ with asyncio for parallel processing
- Azure OpenAI GPT-4o with Structured Outputs (Pydantic models)
- pillow-heif for HEIC → JPEG conversion
- pandas for CSV export

**Processing Flow:**
1. Convert HEIC images to JPEG (Azure OpenAI doesn't support HEIC)
2. Extract contact data using Azure OpenAI vision API in parallel (10 concurrent requests)
3. Export results to JSON (primary) and CSV (secondary)

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Image Format | Convert HEIC → JPEG | Azure OpenAI API doesn't support HEIC natively |
| Azure Model | GPT-4o | Best vision accuracy, supports structured outputs |
| Data Extraction | Structured Outputs (Pydantic) | Guaranteed valid JSON, better accuracy than prompting |
| Parallelism | 10 concurrent requests | Balances speed with Azure rate limits |
| Primary Output | JSON with metadata | Preserves structure, includes processing stats |
| Secondary Output | Flattened CSV | Excel-compatible for easy analysis |

## Project Structure

```
ai-extract-text-image/
├── lead_pics/                    # Input: 125 HEIC images
├── output/
│   ├── converted_images/         # JPEG conversions
│   ├── extracted_contacts.json   # Primary output
│   └── extracted_contacts.csv    # Secondary output
├── src/
│   ├── config.py                 # Configuration and environment
│   ├── models.py                 # Pydantic data models
│   ├── image_converter.py        # HEIC → JPEG conversion
│   ├── batch_processor.py        # Azure OpenAI extraction + parallel processing
│   └── export.py                 # JSON/CSV export utilities
├── main.py                       # Main execution script
├── requirements.txt              # Dependencies
├── .env                          # Azure credentials (gitignored)
└── extraction.log                # Processing logs
```

## Data Schema

**ContactInfo Pydantic Model** (extracted from each image):
- **Primary Contact:** full_name, company_name, job_title
- **Contact Methods:** phone_number, mobile_number, email
- **Address:** address, city, state, zip_code, country
- **Additional:** last_contact_date (from middle of image), website, notes
- **Metadata:** confidence_score (high/medium/low), source_image

**Output JSON Structure:**
```json
{
  "metadata": {
    "total_images": 125,
    "successful": 123,
    "failed": 2,
    "processing_date": "2025-11-25T14:30:00",
    "model_used": "gpt-4o"
  },
  "contacts": [
    {
      "source_image": "IMG_7512.HEIC",
      "full_name": "John Smith",
      "company_name": "Acme Corp",
      "email": "john.smith@acme.com",
      "last_contact_date": "2024-11-15",
      ...
    }
  ],
  "errors": [...]
}
```

## Implementation Steps

### Phase 1: Project Setup
1. Create project structure (src/, output/, tests/)
2. Set up virtual environment: `python3 -m venv venv`
3. Install dependencies from requirements.txt
4. Configure .env file with Azure credentials:
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_DEPLOYMENT_NAME`

### Phase 2: Core Components

**File: src/models.py**
- Define `ContactInfo` Pydantic model with all extraction fields
- Define `ExtractionResult` wrapper model
- Use Field() with descriptions to guide LLM extraction

**File: src/image_converter.py**
- Implement `ImageConverter` class
- Convert HEIC to JPEG at 90% quality
- Resize images > 2048px width to stay under Azure's 20MB limit
- Handle conversion errors gracefully

**File: src/batch_processor.py**
- Implement `BatchProcessor` class with asyncio + Semaphore
- Use `client.beta.chat.completions.parse()` for structured outputs
- Encode images to base64 for API
- Implement retry logic with exponential backoff (3 attempts)
- Add progress tracking with tqdm

**File: src/export.py**
- `export_to_json()`: Create structured JSON with metadata + contacts + errors
- `export_to_csv()`: Flatten JSON to pandas DataFrame and export
- Generate summary CSV with processing statistics

**File: src/config.py**
- Load environment variables with python-dotenv
- Validate required credentials
- Set up project directories
- Configure processing parameters (concurrent requests, JPEG quality, etc.)

**File: main.py**
- Orchestrate 4-step process:
  1. Convert HEIC images
  2. Initialize Azure OpenAI client
  3. Process images in parallel
  4. Export results to JSON and CSV
- Display progress and summary statistics

### Phase 3: Testing & Execution

1. Test with 1-2 sample images first
2. Run full batch of 125 images: `python main.py`
3. Review outputs in `output/` directory
4. Manually verify 10 random extractions for quality
5. Check `extraction.log` for any errors

## Key Technical Details

### HEIC Conversion
```python
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()
img = Image.open("image.HEIC")
rgb_img = img.convert('RGB')  # JPEG requires RGB
rgb_img.save("output.jpg", 'JPEG', quality=90, optimize=True)
```

### Azure OpenAI Structured Outputs
```python
client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": extraction_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "high"  # High detail for accurate extraction
                    }
                }
            ]
        }
    ],
    response_format=ExtractionResult,
    temperature=0.1
)
```

### Parallel Processing with Rate Limiting
```python
async def process_batch(image_paths):
    semaphore = Semaphore(10)  # Max 10 concurrent
    tasks = [process_single_image(path, semaphore) for path in image_paths]
    results = await tqdm_asyncio.gather(*tasks)
    return results
```

## Dependencies (requirements.txt)

```
openai>=1.50.0                    # Azure OpenAI client
pillow>=10.0.0                    # Image processing
pillow-heif>=0.18.0               # HEIC support
pydantic>=2.8.0                   # Data models
asyncio-throttle>=1.0.0           # Rate limiting
tenacity>=8.2.0                   # Retry logic
tqdm>=4.66.0                      # Progress bars
pandas>=2.0.0                     # CSV export
python-dotenv>=1.0.0              # Environment management
pytest>=8.0.0                     # Testing
```

## Error Handling

- **HEIC Conversion Failures:** Log error, skip image, continue processing
- **API Rate Limits (429):** Retry with exponential backoff (4s, 8s, 16s, 32s, 60s)
- **API Errors:** Retry up to 3 times, then mark as failed
- **Validation Errors:** Pydantic handles automatically with structured outputs
- **Failed Extractions:** Saved to JSON errors array for manual review

## Performance Estimates

- **Processing Time:** 5-15 minutes for 125 images (with 10 concurrent requests)
- **Cost:** ~$1.50-$2.50 for GPT-4o (approximate)
- **Success Rate:** Expected >95% with retry logic

## Environment Variables

Create `.env` file:
```bash
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
MAX_CONCURRENT_REQUESTS=10
JPEG_QUALITY=90
MAX_IMAGE_WIDTH=2048
```

## Execution

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Then edit with your credentials

# Run extraction
python main.py

# Output files created:
# - output/extracted_contacts.json
# - output/extracted_contacts.csv
# - output/extracted_contacts_summary.csv
# - extraction.log
```

## Validation Checklist

After extraction:
- [ ] JSON file is valid and contains all contacts
- [ ] CSV opens in Excel with proper formatting
- [ ] Sample 10 random extractions for accuracy
- [ ] Check confidence_score distribution
- [ ] Review failed extractions in errors array
- [ ] Verify last_contact_date field is populated
- [ ] Success rate > 95%

## Critical Files to Create (Priority Order)

1. **src/models.py** - Data schema foundation for structured outputs
2. **src/image_converter.py** - HEIC conversion (must work for all 125 images)
3. **src/batch_processor.py** - Core extraction logic with Azure OpenAI
4. **main.py** - Orchestration and user interface
5. **src/config.py** - Configuration management
6. **src/export.py** - JSON/CSV export utilities
7. **requirements.txt** - Dependency specification
8. **.env.example** - Environment template

## Future Enhancements (Optional)

- Resume capability: Skip already-processed images using SQLite tracking
- Low-confidence review queue: Flag extractions needing manual verification
- Azure Batch API: Use for 50% cost savings (24-hour processing window)
- Data enrichment: Phone formatting, email validation, address geocoding
- HTML report: Generate visual report with image thumbnails
