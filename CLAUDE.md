# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python system that extracts structured contact/lead data from HEIC images using Azure OpenAI GPT-4o vision models with structured outputs (Pydantic). The system converts HEIC → JPEG, processes images in parallel, and exports to JSON/CSV.

## Essential Commands

### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Then add Azure credentials
```

### Run Extraction
```bash
python main.py
```

### Development
```bash
# Type checking
mypy src/

# Run tests
pytest tests/

# Run single test
pytest tests/test_converter.py::test_convert_single
```

## Architecture

### Data Flow Pipeline (4 Stages)
1. **Conversion** (ImageConverter) → HEIC files to JPEG (Azure OpenAI doesn't support HEIC)
2. **Extraction** (BatchProcessor) → Parallel async processing with Azure OpenAI structured outputs
3. **Aggregation** → Combine successful results + track failures separately
4. **Export** → JSON (primary), CSV (secondary), retry list (failures only)

### Critical Design Decisions

**Structured Outputs with Pydantic Models**
- Uses `client.beta.chat.completions.parse()` with `response_format=ExtractionResult`
- Guarantees valid JSON schema compliance (no parsing errors)
- Field descriptions in Pydantic models guide the LLM extraction
- API version must be `2024-08-01-preview` or later for structured outputs

**Error Handling: Individual Image Isolation**
- Each image conversion has try/catch → failures logged, processing continues
- Each image extraction has try/catch → failures recorded with status="failed"
- Failed conversions tracked separately from failed extractions
- System generates `failed_images_retry_list.txt` with both failure types

**Parallel Processing with Rate Limiting**
- Uses asyncio with Semaphore (default 10 concurrent requests)
- Tenacity for exponential backoff retry (3 attempts: 4s, 8s, 16s, 32s, 60s max)
- Azure OpenAI rate limits: ~1,000 RPM, 100k-240k TPM
- Images converted to JPEG with max 2048px width (Azure 20MB limit)

### Key Files and Responsibilities

**src/models.py** - Data schema definition
- `ContactInfo`: All extractable fields (name, company, email, phone, address, etc.)
- `ExtractionResult`: Wrapper with contact + status + error_message
- Field descriptions are critical - they instruct the LLM what to extract

**src/config.py** - Configuration singleton
- Auto-creates `output/` and `output/converted_images/` directories
- Validates Azure credentials on init (raises ValueError if missing)
- Uses python-dotenv for .env loading
- Project paths resolved from `Path(__file__).parent.parent`

**src/image_converter.py** - HEIC conversion
- `convert_all()` returns tuple: `(List[Path], List[Dict])` = (successful paths, failures)
- Failures include: filename, error message, stage="conversion"
- Uses pillow-heif with `register_heif_opener()` before any Image.open()

**src/batch_processor.py** - Core extraction engine
- `process_batch()`: Async gather with tqdm progress bar
- `extract_contact()`: Has @retry decorator for API resilience
- Images encoded to base64 before sending to Azure
- Maps JPEG paths back to original HEIC filenames in output

**src/export.py** - Multi-format output
- `export_to_json()`: Structured output with metadata + contacts + errors arrays
- `export_to_csv()`: Flattened DataFrame with column reordering for readability
- `create_retry_list()`: Human-readable text file with failed image filenames

**main.py** - Orchestration
- 4-step pipeline with progress reporting
- Handles both conversion failures AND extraction failures
- Creates retry list only if failures exist
- Logging to both file (extraction.log) and console

## Environment Variables

Required in `.env`:
```bash
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

Optional (with defaults):
```bash
MAX_CONCURRENT_REQUESTS=10
JPEG_QUALITY=90
MAX_IMAGE_WIDTH=2048
```

## Input/Output Conventions

**Input:** `lead_pics/` directory with `.HEIC` or `.heic` files

**Output Directory:** `output/`
- `extracted_contacts.json` - Full structured data
- `extracted_contacts.csv` - Flattened for Excel
- `extracted_contacts_summary.csv` - Processing stats
- `failed_images_retry_list.txt` - Failed images (if any)
- `converted_images/*.jpg` - JPEG conversions
- `../extraction.log` - Detailed logs (project root)

## Modifying the Data Schema

To add/change extracted fields:

1. Update `src/models.py` → Add field to `ContactInfo` with description
2. Field description guides LLM extraction (be specific)
3. No changes needed elsewhere - structured outputs handle new fields automatically
4. CSV export in `src/export.py` may need column reordering if new field should be prominent

Example:
```python
# src/models.py
class ContactInfo(BaseModel):
    linkedin_url: Optional[str] = Field(
        None,
        description="LinkedIn profile URL if visible in image"
    )
```

## Azure OpenAI API Details

**Structured Outputs Call Pattern:**
```python
response = client.beta.chat.completions.parse(
    model=config.model_name,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"  # Critical for accuracy
                }
            }
        ]
    }],
    response_format=ExtractionResult,  # Pydantic model
    temperature=0.1  # Low for consistency
)
```

**Extraction Prompt Strategy:**
- Emphasizes LEFT SIDE for primary contact details
- Highlights MIDDLE AREA for "last_contact_date"
- Instructs to set null for missing/unclear fields
- Requests confidence_score based on image clarity

## Common Failure Scenarios

**"No images were converted"**
- Check `lead_pics/` exists and contains `.HEIC` files
- Verify file permissions

**"AZURE_OPENAI_API_KEY not set"**
- `.env` file missing or not in project root
- Virtual environment not activated

**Rate limit errors (429)**
- Reduce MAX_CONCURRENT_REQUESTS in `.env`
- System auto-retries with backoff, but may need lower concurrency

**Import errors**
- Virtual environment not activated: `source venv/bin/activate`
- Dependencies not installed: `pip install -r requirements.txt`

## Performance Characteristics

- 125 images: ~5-15 minutes processing time
- Estimated cost: $1.50-$2.50 (GPT-4o vision pricing)
- Expected success rate: >95% with retry logic
- Conversion step is fast (~1-2 min), extraction is the bottleneck
