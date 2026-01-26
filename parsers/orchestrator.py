from parsers.qr_parser import QRParser
from parsers.regex_parser import RegexParser
from dtos.models import InvoiceData

class Orchestrator:
    def __init__(self, pdf_path: str, raw_text: str):
        self.pdf_path = pdf_path
        self.raw_text = raw_text
        self.regex_parser = RegexParser(raw_text)
        self.qr_parser = QRParser(pdf_path)

    def parse(self) -> InvoiceData | None:
        # Primero intento con QR
        qr_data = self.qr_parser.extract_and_parse()
        if qr_data:
            qr_data = self._enrich_qr_with_regex(qr_data)
            return qr_data
        else:
            # Sin QR o invalido, usando regex.
            regex_data = self.regex_parser.extract_data()
            return regex_data
        
    def _enrich_qr_with_regex(self, qr_data: InvoiceData) -> InvoiceData:
        # El importe neto no viene en el qr
        regex_importes = self.regex_parser.extract_importes()
        qr_data.importe_neto = regex_importes.importe_neto

        # La letra no siempre es la correcta.
        letra = self.regex_parser.extract_letra()
        if letra and letra != qr_data.letra:
            qr_data.letra = letra

        # OC
        oc = self.regex_parser.extract_oc()
        qr_data.orden_compra = oc

        return qr_data