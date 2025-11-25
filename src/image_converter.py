"""HEIC to JPEG image conversion utilities"""

from PIL import Image
import pillow_heif
from pathlib import Path
import logging
from typing import List, Dict

pillow_heif.register_heif_opener()
logger = logging.getLogger(__name__)


class ImageConverter:
    """Handles HEIC to JPEG conversion"""

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        quality: int = 90,
        max_width: int = 2048
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.quality = quality
        self.max_width = max_width
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_single(self, heic_path: Path) -> Path:
        """Convert single HEIC image to JPEG

        Args:
            heic_path: Path to HEIC image

        Returns:
            Path to converted JPEG image

        Raises:
            Exception: If conversion fails
        """
        try:
            # Open HEIC image
            img = Image.open(heic_path)

            # Convert to RGB (required for JPEG)
            rgb_img = img.convert('RGB')

            # Resize if too large
            if rgb_img.width > self.max_width:
                ratio = self.max_width / rgb_img.width
                new_size = (self.max_width, int(rgb_img.height * ratio))
                rgb_img = rgb_img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized {heic_path.name} to {new_size}")

            # Create output path
            output_path = self.output_dir / f"{heic_path.stem}.jpg"

            # Save as JPEG
            rgb_img.save(
                output_path,
                'JPEG',
                quality=self.quality,
                optimize=True
            )
            logger.info(f"Converted {heic_path.name} -> {output_path.name}")

            return output_path

        except Exception as e:
            logger.error(f"Failed to convert {heic_path}: {str(e)}")
            raise

    def convert_all(self) -> tuple[List[Path], List[Dict]]:
        """Convert all HEIC images in input directory

        Returns:
            Tuple of (converted image paths, conversion failures)
        """
        heic_files = (
            list(self.input_dir.glob("*.HEIC")) +
            list(self.input_dir.glob("*.heic"))
        )
        converted = []
        failed_conversions = []

        logger.info(f"Found {len(heic_files)} HEIC files to convert")

        for heic_file in heic_files:
            try:
                output_path = self.convert_single(heic_file)
                converted.append(output_path)
            except Exception as e:
                error_msg = f"Skipping {heic_file.name}: {str(e)}"
                logger.error(error_msg)
                failed_conversions.append({
                    "filename": heic_file.name,
                    "error": str(e),
                    "stage": "conversion"
                })

        logger.info(
            f"Successfully converted {len(converted)}/{len(heic_files)} images"
        )
        if failed_conversions:
            logger.warning(f"Failed to convert {len(failed_conversions)} images")

        return converted, failed_conversions
