"""OCR service using EasyOCR for text extraction from images."""

import logging
import sys
from io import BytesIO
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

# Global reader instance (lazy initialization)
_reader: Optional[object] = None


def _get_ocr_reader():
	"""Get or initialize the EasyOCR reader (singleton pattern).
	
	Initializes on first call. Downloads language models on first use.
	Models are cached locally to avoid repeated downloads.
	"""
	global _reader
	
	if _reader is None:
		try:
			import easyocr
			logger.info("Initializing EasyOCR reader for English...")
			_reader = easyocr.Reader(
				["en"],
				gpu=False,  # Set to True if GPU is available in your environment
				verbose=False,
			)
			logger.info("✓ EasyOCR reader initialized successfully")
		except ImportError:
			install_cmd = f'"{sys.executable}" -m pip install easyocr==1.7.2'
			logger.error(
				"EasyOCR not installed in this interpreter: %s. Install with: %s",
				sys.executable,
				install_cmd,
			)
			raise RuntimeError("EasyOCR is required but not installed")
		except Exception as e:
			logger.error(f"Failed to initialize EasyOCR reader: {e}")
			raise RuntimeError(f"EasyOCR initialization failed: {e}")
	
	return _reader


def extract_text_from_image(image_bytes: bytes) -> str:
	"""Extract text from image bytes using EasyOCR.
	
	Args:
		image_bytes: Raw image file bytes (PNG, JPEG, etc.)
	
	Returns:
		Extracted text as a single string
	
	Raises:
		RuntimeError: If OCR fails or EasyOCR is not available
		ValueError: If image is invalid
	"""
	try:
		# Open image
		try:
			with Image.open(BytesIO(image_bytes)) as img:
				# Convert RGBA to RGB if needed
				if img.mode in ("RGBA", "LA", "P"):
					rgb_img = Image.new("RGB", img.size, (255, 255, 255))
					rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
					img = rgb_img
				
				# Convert PIL image to numpy array for EasyOCR
				import numpy as np
				image_array = np.array(img)
		except Exception as e:
			logger.error(f"Failed to open image: {e}")
			raise ValueError(f"Invalid image file: {e}")
		
		# Get OCR reader
		reader = _get_ocr_reader()
		
		# Perform OCR
		logger.debug("Running EasyOCR on image...")
		results = reader.readtext(image_array, detail=0)  # detail=0 returns only text
		
		# Combine all detected text with line breaks
		extracted_text = "\n".join(results).strip()
		
		if not extracted_text:
			logger.warning("No text detected in image")
			return ""
		
		logger.debug(f"Extracted {len(extracted_text)} characters from image")
		return extracted_text
	
	except ValueError:
		raise
	except Exception as e:
		logger.error(f"OCR processing failed: {type(e).__name__}: {str(e)}")
		raise RuntimeError(f"Failed to extract text from image: {e}")
