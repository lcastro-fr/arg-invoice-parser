import argparse
from pathlib import Path
from core import extract_text_from_pdf, setup_logging
from parsers import Orchestrator


def main():
    parser = argparse.ArgumentParser(description="Invoice Parser")
    parser.add_argument(
        "--pdf", type=str, required=True, help="Ruta al archivo PDF de la factura"
    )
    parser.add_argument("--debug", action="store_true", help="Debug")
    args = parser.parse_args()

    logger = setup_logging(debug=args.debug)

    if not Path(args.pdf).is_file():
        logger.error(f"Archivo no encontrado: {args.pdf}")
        exit(1)

    raw_text = extract_text_from_pdf(args.pdf)
    logger.info(f"Texto extraído del PDF: {raw_text}")

    if not raw_text:
        logger.error("No se extrajo texto del PDF.")
        exit(1)

    orchestrator = Orchestrator(pdf_path=args.pdf, raw_text=raw_text)
    invoice_data = orchestrator.parse()
    if not invoice_data:
        logger.error("No obtuvimos datos de la factura.")
        exit(1)
    
    logger.info("Datos extraídos de la factura:")
    logger.info(invoice_data)


if __name__ == "__main__":
    main()
