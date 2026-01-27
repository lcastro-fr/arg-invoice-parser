from urllib.parse import parse_qs, urlparse
import base64
import json
import pymupdf
from PIL import Image
from pyzbar.pyzbar import decode
import io
import logging
from dtos import InvoiceData

logger = logging.getLogger(__name__)


class QRParser:
    def __init__(self, file_content: io.BytesIO):
        self.file_content = file_content
        self.invoice_data = InvoiceData()

    def _decode_afip_qr(self, url) -> dict | None:
        try:
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)

            if "p" in params:
                base64_data = params["p"][0]
                decoded_bytes = base64.b64decode(base64_data)
                json_str = decoded_bytes.decode("utf-8")
                data = json.loads(json_str)
                pto_venta = str(data.get("ptoVta", "")).zfill(4)
                nro_cmp = str(data.get("nroCmp", "")).zfill(8)
                referencia = f"{pto_venta}-{nro_cmp}"
                moneda = "USD" if data.get("moneda") == "DOL" else "ARS"

                return {
                    "fecha": data.get("fecha"),
                    "cuit": str(data.get("cuit")),
                    "referencia": referencia,
                    "importe_neto": None,
                    "moneda": moneda,
                    "tipo_cmp": int(data.get("tipoCmp"))
                    if data.get("tipoCmp")
                    else None,
                    "letra": data.get("tipoCodAut"),
                    "importe_bruto": data.get("importe"),
                }
        except Exception as e:
            logger.error(f"Error decoding AFIP QR: {e}")
            return None

    def extract_and_parse(self) -> InvoiceData | None:
        """
        Look for QR code.
        """
        try:
            doc = pymupdf.open(stream=self.file_content)
            if not doc:
                return None
        except Exception as e:
            logger.error(f"Error opening PDF: {e}")
            return None

        try:
            for page_num in range(len(doc)):
                images = doc[page_num].get_images(full=True)

                if not images:
                    continue

                # List of QR founded
                for img_index, img in enumerate(images):
                    base_image = doc.extract_image(img[0])
                    image_bytes = base_image["image"]
                    image = Image.open(io.BytesIO(image_bytes))
                    qr_codes = decode(image)

                    if not qr_codes:
                        continue

                    for qr_code in qr_codes:
                        qr_data = qr_code.data.decode("utf-8")
                        if "arca.gob.ar" in qr_data or "afip.gob.ar" in qr_data:
                            afip_data = self._decode_afip_qr(qr_data)
                            if afip_data:
                                return InvoiceData(**afip_data, qr_decoded=True)
        except Exception as e:
            logger.error(f"Error extracting QR codes: {e}")
            return None
