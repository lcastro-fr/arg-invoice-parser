from parsers import Orchestrator
from core import extract_text_from_pdf, setup_logging
from pathlib import Path
import glob
import pandas as pd
import time

def main():
    """Run batch processing of invoices in a directory and save results to excel."""
    try:
        logger = setup_logging()
        input_dir = Path("/app/invoices")
        output_file = Path("/app/output/invoice_data.xlsx")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        all_invoice_data = []
        pdf_files = glob.glob(str(input_dir / "*.pdf"))

        for pdf_path in pdf_files:
            raw_text = extract_text_from_pdf(pdf_path)
            if not raw_text:
                logger.warning(f"No se pudo extraer texto de {pdf_path}")
                continue
            
            current_time = time.time()
            orchestrator = Orchestrator(pdf_path=pdf_path, raw_text=raw_text)
            invoice_data = orchestrator.parse()
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
            logger.info(f"Datos de facturas guardados en {output_file}")
        else:
            logger.info("No se extrajeron datos de facturas.")
    except Exception as e:
        logger.error(f"Error en el procesamiento por lotes: {e}")


if __name__ == "__main__":
    main()
