import logging
from io import BytesIO

from dtos import InvoiceData
from infrastructure.ports.invoices_wh_port import InvoicesWHPort
from parsers import OCRParser, QRParser, RegexParser

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
        ocr_parser = OCRParser(file_content)
        raw_text = ocr_parser.extract_digital_text()
        if not raw_text:
            return None

        if verbose:
            logging.info(f"Extracted digital text from PDF: {raw_text}")

        qr_parser = QRParser(file_content)
        qr_data = qr_parser.extract_and_parse()

        regex_parser = RegexParser(raw_text, own_cuit=own_cuit)

        letra = regex_parser.extract_letra()
        cuit = (qr_data.cuit if qr_data else None) or regex_parser.extract_cuit()
        referencia = (
            qr_data.referencia if qr_data else None
        ) or regex_parser.extract_referencia()

        ocr_content: str | None = None
        ocr_regex_parser: RegexParser | None = None
        if not letra or not cuit or not referencia:
            ocr_content = ocr_parser.extract_text_with_ocr()
            if ocr_content:
                ocr_regex_parser = RegexParser(ocr_content, own_cuit=own_cuit)
                if not letra:
                    letra = ocr_regex_parser.extract_letra()
                if not cuit:
                    cuit = ocr_regex_parser.extract_cuit()
                if not referencia:
                    referencia = ocr_regex_parser.extract_referencia()

        if letra and cuit and referencia and self.invoices_wh_port:
            db_data = self.invoices_wh_port.get_invoice(referencia, cuit, letra)
            if db_data:
                return self._enrich_with_regex(db_data, regex_parser)

        if qr_data:
            if letra:
                qr_data.letra = letra
            return self._enrich_with_regex(qr_data, regex_parser)

        invoice_data = regex_parser.extract_data()
        if letra:
            invoice_data.letra = letra
        if cuit:
            invoice_data.cuit = cuit
        if referencia:
            invoice_data.referencia = referencia

        if not invoice_data.tipo_cmp or not invoice_data.fecha:
            if not ocr_content:
                ocr_content = ocr_parser.extract_text_with_ocr()
            if ocr_content:
                if not ocr_regex_parser:
                    ocr_regex_parser = RegexParser(ocr_content, own_cuit=own_cuit)
                if not invoice_data.tipo_cmp:
                    invoice_data.tipo_cmp = ocr_regex_parser.extract_tipo_cmp()
                if not invoice_data.fecha:
                    invoice_data.fecha = ocr_regex_parser.extract_fecha()

        return invoice_data

    @staticmethod
    def _enrich_with_regex(data: InvoiceData, regex_parser: RegexParser) -> InvoiceData:
        if not data.importe_neto or not data.importe_bruto:
            importes = regex_parser.extract_importes(gross_amount=data.importe_bruto)
            if not data.importe_neto:
                data.importe_neto = importes.importe_neto
            if not data.importe_bruto:
                data.importe_bruto = importes.importe_bruto
        if not data.letra:
            data.letra = regex_parser.extract_letra()
        if not data.orden_compra:
            data.orden_compra = regex_parser.extract_oc()
        return data
