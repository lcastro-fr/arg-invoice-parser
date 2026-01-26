import pdfplumber
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from io import BytesIO


class OCRService:
    def __init__(self, file_content: "BytesIO"):
        self.file_content = file_content

    def extract_text(self) -> str | None:
        text = ""
        with pdfplumber.open(self.file_content) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text if len(text.strip()) > 50 else None
