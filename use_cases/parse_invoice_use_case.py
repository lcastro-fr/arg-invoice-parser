import logging
from io import BytesIO

from dtos import InvoiceData
from infrastructure.ports.invoices_wh_port import InvoicesWHPort
from services import DataExtractionService, OCRService

logger = logging.getLogger(__name__)


class ParseInvoiceUseCase:
    def __init__(self, invoices_wh_port: InvoicesWHPort | None = None):
        self.invoices_wh_port = invoices_wh_port

    @staticmethod
    def _create_adapter_from_env() -> InvoicesWHPort | None:
        try:
            from infrastructure.adapters.invoices_wh_adaptar import InvoicesWHAdapter
            from infrastructure.config.database_config import DATABASE_URL

            if DATABASE_URL:
                return InvoicesWHAdapter(DATABASE_URL)
        except Exception as e:
            logger.warning(f"Failed to initialize DB adapter: {e}")
        return None

    def parse_invoice(
        self, file_content: BytesIO, own_cuit: str | None = None, verbose: bool = False
    ) -> InvoiceData | None:
        # Extract text via OCR
        ocr_service = OCRService(file_content)
        raw_text = ocr_service.extract_digital_text()
        if not raw_text:
            return None

        if verbose:
            logging.info(f"Extracted digital text from PDF: {raw_text}")

        # Extract data via DataExtractionService
        data_extraction_service = DataExtractionService(
            file_content=file_content,
            raw_text=raw_text,
            own_cuit=own_cuit,
            invoices_wh_port=self.invoices_wh_port,
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
