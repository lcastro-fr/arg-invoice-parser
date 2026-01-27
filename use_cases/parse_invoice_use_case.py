from services import OCRService, DataExtractionService
from io import BytesIO
from dtos import InvoiceData


class ParseInvoiceUseCase:
    @staticmethod
    def parse_invoice(
        file_content: BytesIO, own_cuit: str | None = None
    ) -> InvoiceData | None:
        # Extract text via OCR
        ocr_service = OCRService(file_content)
        raw_text = ocr_service.extract_text()
        if not raw_text:
            return None

        # Extract data via DataExtractionService
        data_extraction_service = DataExtractionService(
            file_content=file_content, raw_text=raw_text, own_cuit=own_cuit
        )
        invoice_data = data_extraction_service.parse()
        if not invoice_data:
            return None

        return invoice_data
