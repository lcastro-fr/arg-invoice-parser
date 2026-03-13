from io import BytesIO

from dtos import InvoiceData
from infrastructure.ports.invoices_wh_port import InvoicesWHPort
from parsers import QRParser, RegexParser


class DataExtractionService:
    def __init__(
        self,
        file_content: BytesIO,
        raw_text: str,
        own_cuit: str | None = None,
        invoices_wh_port: InvoicesWHPort | None = None,
    ):
        self.regex_parser = RegexParser(raw_text, own_cuit=own_cuit)
        self.qr_parser = QRParser(file_content)
        self.invoices_wh_port = invoices_wh_port

    def parse(self) -> InvoiceData | None:
        qr_data = self.qr_parser.extract_and_parse()

        letra = self.regex_parser.extract_letra()
        cuit = (qr_data.cuit if qr_data else None) or self.regex_parser.extract_cuit()
        referencia = (
            qr_data.referencia if qr_data else None
        ) or self.regex_parser.extract_referencia()

        # Try DB lookup if we have all three keys
        if cuit and referencia and letra and self.invoices_wh_port:
            db_data = self.invoices_wh_port.get_invoice(referencia, cuit, letra)
            if db_data:
                return self._enrich_with_regex(db_data)

        # DB miss or not configured: use QR data if available
        if qr_data:
            if letra:
                qr_data.letra = letra
            return self._enrich_with_regex(qr_data)

        # Full regex parsing as last resort
        return self.regex_parser.extract_data()

    def _enrich_with_regex(self, data: InvoiceData) -> InvoiceData:
        if not data.importe_neto:
            importes = self.regex_parser.extract_importes(
                gross_amount=data.importe_bruto
            )
            data.importe_neto = importes.importe_neto
        if not data.letra:
            data.letra = self.regex_parser.extract_letra()
        if not data.orden_compra:
            data.orden_compra = self.regex_parser.extract_oc()
        return data
