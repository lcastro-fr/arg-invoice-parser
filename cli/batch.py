"""Batch invoice processing CLI."""

from pathlib import Path
import glob
import pandas as pd
import time
from io import BytesIO
from utils import setup_logging
from use_cases import ParseInvoiceUseCase
import argparse


def main():
    """Run batch processing of invoices in a directory and save results to excel."""
    parser = argparse.ArgumentParser(description="Invoice Parser")
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Ruta al directorio con archivos PDF de facturas",
    )
    parser.add_argument(
        "--output_file", type=str, required=True, help="Ruta al archivo Excel de salida"
    )
    parser.add_argument("--debug", action="store_true", help="Debug")
    args = parser.parse_args()

    try:
        logger = setup_logging()
        input_dir = Path(args.input_dir)
        output_file = Path(args.output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        all_invoice_data = []
        pdf_files = glob.glob(str(input_dir / "*.pdf"))

        for pdf_path in pdf_files:
            if not Path(pdf_path).exists():
                logger.warning(f"File not found: {pdf_path}")
                continue

            with open(pdf_path, "rb") as f:
                file_content = BytesIO(f.read())

            current_time = time.time()
            invoice_data = ParseInvoiceUseCase.parse_invoice(file_content)
            if invoice_data:
                data_dict = invoice_data.model_dump()
                data_dict["pdf_path"] = pdf_path
                elapsed_time = time.time() - current_time
                data_dict["processing_time_sec"] = round(elapsed_time, 2)
                logger.info(f"Procesada {pdf_path} en {elapsed_time:.2f} segundos")
                all_invoice_data.append(data_dict)

        if all_invoice_data:
            df = pd.DataFrame(all_invoice_data)
            df.to_excel(output_file, index=False)
            logger.info(f"Invoice data saved to {output_file}")
        else:
            logger.info("No invoice data extracted.")
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")


if __name__ == "__main__":
    main()
