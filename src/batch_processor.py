"""Batch processing with parallel execution and rate limit handling"""

import asyncio
from asyncio import Semaphore
from pathlib import Path
import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm.asyncio import tqdm_asyncio
from openai import AzureOpenAI
import base64

from .models import ExtractionResult

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Process multiple images with controlled parallelism"""

    def __init__(
        self,
        client: AzureOpenAI,
        model_name: str,
        max_concurrent: int = 10
    ):
        self.client = client
        self.model_name = model_name
        self.semaphore = Semaphore(max_concurrent)

    def encode_image(self, image_path: Path) -> str:
        """Encode image to base64 string

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def extract_contact(self, image_path: Path) -> ExtractionResult:
        """Extract contact data from single image with retry logic

        Args:
            image_path: Path to JPEG image

        Returns:
            ExtractionResult with contact data

        Raises:
            Exception: If extraction fails after retries
        """
        # Encode image
        base64_image = self.encode_image(image_path)

        # Create extraction prompt
        prompt = """Extract all visible contact and lead information from this image.

Instructions:
- Focus on the LEFT SIDE for primary contact details (name, company, phone, email, address)
- Look for "last date of contact" or similar date fields in the MIDDLE area
- Extract ALL visible fields accurately
- If a field is not visible, unclear, or empty, set it to null
- Provide a confidence score: 'high' if image is clear and most fields are visible,
  'medium' if some fields are unclear, 'low' if image quality is poor

Be thorough and accurate in your extraction."""

        # Make API call with structured output
        response = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format=ExtractionResult,
            temperature=0.1
        )

        return response.choices[0].message.parsed

    async def process_single_image(self, image_path: Path) -> Dict:
        """Process single image asynchronously

        Args:
            image_path: Path to JPEG image

        Returns:
            Dictionary with status and extracted data or error
        """
        async with self.semaphore:
            try:
                # Run extraction in thread pool
                result = await asyncio.to_thread(
                    self.extract_contact,
                    image_path
                )

                # Build response
                contact_data = result.contact.model_dump()
                # Map back to original HEIC filename
                contact_data['source_image'] = image_path.stem + '.HEIC'

                return {
                    "status": "success",
                    "data": contact_data,
                    "error": None
                }

            except Exception as e:
                logger.error(f"Failed to process {image_path.name}: {str(e)}")
                return {
                    "status": "failed",
                    "data": {"source_image": image_path.stem + '.HEIC'},
                    "error": str(e)
                }

    async def process_batch(self, image_paths: List[Path]) -> List[Dict]:
        """Process batch of images with progress tracking

        Args:
            image_paths: List of paths to JPEG images

        Returns:
            List of dictionaries with extraction results
        """
        tasks = [self.process_single_image(path) for path in image_paths]
        results = await tqdm_asyncio.gather(
            *tasks,
            desc="Extracting contact data",
            total=len(image_paths)
        )
        return results
