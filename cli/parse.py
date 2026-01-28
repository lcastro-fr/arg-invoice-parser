"""Single invoice parser CLI."""

import argparse
from pathlib import Path
from io import BytesIO
from utils import setup_logging
from use_cases import ParseInvoiceUseCase


def main():
    parser = argparse.ArgumentParser(description="Invoice Parser")
    parser.add_argument(
        "--pdf", type=str, required=True, help="Path to the invoice PDF file"
    )
    parser.add_argument("--cuit", type=str, help="Own CUIT number", default=None)
    parser.add_argument("--debug", action="store_true", help="Debug")
    args = parser.parse_args()

    logger = setup_logging(debug=args.debug)

    if not Path(args.pdf).is_file():
        logger.error(f"File not found: {args.pdf}")
        exit(1)

    with open(args.pdf, "rb") as f:
        file_content = BytesIO(f.read())

    try:
        invoice_data = ParseInvoiceUseCase.parse_invoice(
            file_content, own_cuit=args.cuit
        )
        if invoice_data:
            logger.info(f"Extracted data: {invoice_data}")
        else:
            logger.warning("No data could be extracted from the invoice.")
    except Exception as e:
        logger.error(f"Error parsing the invoice: {e}")


if __name__ == "__main__":
    main()
