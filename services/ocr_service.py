import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from io import BytesIO


class OCRService:
    def __init__(self, file_content: "BytesIO"):
        self.file_content = file_content

    def extract_digital_text(self) -> str | None:
        text = ""
        with pdfplumber.open(self.file_content) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text if len(text.strip()) > 50 else None

    def extract_text_with_ocr(self) -> str:
        """Extract text from PDF using OCR (limited to first page header)."""
        text = ""
        images = convert_from_bytes(
            self.file_content.getvalue(), first_page=1, last_page=1, fmt="jpeg"
        )
        if not images:
            return text

        page_image = images[0]

        # Crop first 30% of the image
        width, height = page_image.size
        cropped_image = page_image.crop(
            (0, 0, width, height * 0.3)
        )  # left, upper, right, lower
        return pytesseract.image_to_string(cropped_image, config="--psm 6")
