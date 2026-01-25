import pdfplumber
from parsers import AIParser, RegexParser, QRParser
from pprint import pprint
import logging
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    """Text Extraction"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text if len(text.strip()) > 50 else None


def logging_config():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger()


def main():
    logger = logging_config()

    import argparse

    parser = argparse.ArgumentParser(description="Invoice Parser")
    parser.add_argument(
        "--pdf", type=str, required=True, help="Path to the PDF invoice"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if not Path(args.pdf).is_file():
        logger.error(f"File not found: {args.pdf}")
        exit(1)

    raw_text = extract_text_from_pdf(args.pdf)

    if not raw_text:
        logger.error("No text extracted from PDF.")
        exit(1)

    regex_parser = RegexParser(raw_text)

    # Primero intento con QR
    qr_parser = QRParser(args.pdf)
    qr_data = qr_parser.extract_and_parse()
    if qr_data:
        # El importe neto no viene en el qr
        regex_importes = regex_parser.extract_importes()
        qr_data["importe_neto"] = regex_importes["importe_neto"]
        qr_data["debug"] = regex_importes.get("debug", {})

        # La letra no siempre es la correcta.
        letra = regex_parser.extract_letra()
        if letra and letra != qr_data.get("tipoCodAut"):
            qr_data["tipoCodAut"] = letra

        # OC
        oc = regex_parser.extract_oc()
        qr_data["orden_compra"] = oc

        print("QR:")
        pprint(qr_data, indent=2)
    else:
        print("No hay un QR valido, vamos con Regex.")
        regex_data = regex_parser.extract_data()
        print("Regex:")
        pprint(regex_data, indent=2)

        # # Finalmente, si falta algo, uso AI
        # ai_parser = AIParser(raw_text, model=VISION_MODEL)
        # ai_data = ai_parser.parse()
        # print("Data extracted with AI:")
        # print(ai_data)


if __name__ == "__main__":
    main()
