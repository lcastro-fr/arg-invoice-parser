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
        raw_text = ocr_service.extract_digital_text()
        if not raw_text:
            return None

        # Extract data via DataExtractionService
        data_extraction_service = DataExtractionService(
            file_content=file_content, raw_text=raw_text, own_cuit=own_cuit
        )
        invoice_data = data_extraction_service.parse()
        if not invoice_data:
            return None

        # If no cuit, tipo_cmp, letra or fecha found, try to extract via OCR from the header
        if not invoice_data.cuit or not invoice_data.tipo_cmp or not invoice_data.letra:
            ocr_text = ocr_service.extract_text_with_ocr()
            if ocr_text:
                ocr_data_extraction_service = DataExtractionService(
                    file_content=file_content, raw_text=ocr_text, own_cuit=own_cuit
                )
                ocr_invoice_data = ocr_data_extraction_service.parse()
                if ocr_invoice_data:
                    if not invoice_data.cuit:
                        invoice_data.cuit = ocr_invoice_data.cuit
                    if not invoice_data.tipo_cmp:
                        invoice_data.tipo_cmp = ocr_invoice_data.tipo_cmp
                    if not invoice_data.letra:
                        invoice_data.letra = ocr_invoice_data.letra
                    if not invoice_data.fecha:
                        invoice_data.fecha = ocr_invoice_data.fecha

        return invoice_data
