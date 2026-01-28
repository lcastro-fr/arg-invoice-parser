from urllib.parse import parse_qs, urlparse
import base64
import json
import pymupdf
from PIL import Image, ImageOps, ImageEnhance
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

    def _try_decode_with_enhancements(self, pil_image: Image.Image):
        """Try to decode QR code with image enhancements."""
        width, height = pil_image.size
        if width < 60 or height < 60:
            return None  # Too small to be a QR code

        # Try original image with border added
        try:
            img_fast = ImageOps.expand(pil_image, border=20, fill="white")
            decoded = decode(img_fast)
            if decoded:
                return decoded
        except Exception:
            pass

        try:
            # A. Resize: Zoom x2

            img_heavy = img_fast.resize(
                (width * 2, height * 2), Image.Resampling.LANCZOS
            )

            # B. Binarize: Convert to pure Black/White (High Contrast)
            img_heavy = img_heavy.convert("L").point(
                lambda x: 0 if x < 128 else 255, "1"
            )

            # C. Border: Add the quiet zone again (resizing eats margins)
            img_heavy = ImageOps.expand(img_heavy, border=30, fill="white")

            decoded = decode(img_heavy)
            if decoded:
                return decoded

        except Exception:
            pass

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
                for img_index, img in enumerate(
                    reversed(images)
                ):  # QR is usually at the end
                    base_image = doc.extract_image(img[0])
                    image_bytes = base_image["image"]
                    image = Image.open(io.BytesIO(image_bytes))
                    qr_codes = self._try_decode_with_enhancements(image)

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
