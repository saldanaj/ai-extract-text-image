"""Configuration management for the extraction system"""

import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration container for extraction system"""

    def __init__(self):
        load_dotenv()

        # Project directories
        self.project_root = Path(__file__).parent.parent
        self.input_dir = self.project_root / "lead_pics"
        self.output_dir = self.project_root / "output"
        self.converted_dir = self.output_dir / "converted_images"

        # Create directories
        self.output_dir.mkdir(exist_ok=True)
        self.converted_dir.mkdir(exist_ok=True)

        # Azure OpenAI credentials
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        self.api_version = "2024-08-01-preview"

        # Validate required credentials
        if not self.api_key:
            raise ValueError(
                "AZURE_OPENAI_API_KEY not set in environment. "
                "Please copy .env.example to .env and add your credentials."
            )
        if not self.endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT not set in environment. "
                "Please copy .env.example to .env and add your credentials."
            )

        # Processing parameters
        self.max_concurrent = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        self.jpeg_quality = int(os.getenv("JPEG_QUALITY", "90"))
        self.max_image_width = int(os.getenv("MAX_IMAGE_WIDTH", "2048"))

        # Model parameters
        self.temperature = 0.1
        self.detail_level = "high"  # "low" or "high" for vision
