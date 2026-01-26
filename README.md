# OCR Facturas

Invoice parser with multi-strategy extraction for Argentine invoices (AFIP format). Extracts structured data from PDF invoices using QR codes and regex patterns.

## Features

- **Multi-Strategy Parsing**: QR code → Regex fallback chain
- **REST API**: FastAPI endpoint for invoice processing
- **CLI Tools**: Single file and batch processing capabilities
- **Data Validation**: Pydantic models with built-in validation rules
- **Batch Processing**: Process multiple invoices and export to Excel
- **Docker Support**: Containerized deployment ready
- **AFIP Compliance**: Handles Argentine tax authority invoice formats

## Extracted Data

The parser extracts the following fields from invoices:

- `referencia`: Invoice reference number
- `fecha`: Invoice date
- `cuit`: Tax identification number (CUIT)
- `importe_bruto`: Gross amount
- `importe_neto`: Net amount
- `moneda`: Currency
- `tipo_cmp`: Document type
- `letra`: Invoice letter
- `orden_compra`: Purchase order number
- `qr_decoded`: QR decoded flag
- `check`: Validation status

## Project Structure

```
ocr-facturas/
├── api/                    # FastAPI application
│   ├── main.py            # API endpoints
│   └── dtos.py            # API response models
├── cli/                    # Command-line tools
│   ├── parse.py           # Single invoice parser
│   └── batch.py           # Batch processor
│   └── run_api.py         # API runner script
├── parsers/                # Parsing strategies
│   ├── qr_parser.py       # QR code extraction
│   ├── regex_parser.py    # Pattern-based extraction
│   ├── ai_parser.py       # AI-based extraction (Ollama)
│   └── orchestrator.py    # Strategy orchestrator (deprecated)
├── services/               # Business logic layer
│   ├── ocr_service.py     # PDF text extraction
│   └── data_extraction_service.py  # Parser orchestration
├── use_cases/              # Use case layer
│   └── parse_invoice_use_case.py   # Main invoice parsing flow
├── dtos/                   # Data models
│   └── models.py          # Pydantic models
├── utils/                  # Utilities
│   └── core.py            # Logging setup
├── tests/                  # Test suite
```

## Installation

### Using uv

```bash
# Clone the repository
git clone <repository-url>
cd ocr-facturas

# Install dependencies
uv sync

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update && apt-get install -y libzbar0 poppler-utils libmupdf-dev

```
#### Optional: build the project
```bash
uv build
```

## Usage

### CLI Tools

#### Parse Single Invoice

```bash
# Using module syntax
uv run python -m cli.parse --pdf invoices/invoice.pdf

# With debug logging
uv run python -m cli.parse --pdf invoices/invoice.pdf --debug

# Using installed command
uv run invoice-parse --pdf invoices/invoice.pdf
```

#### Batch Processing

Process all PDFs in a directory and export to Excel:

```bash
# Using module syntax
uv run python -m cli.batch

# Using installed command
uv run invoice-batch --input_dir /invoices --output_file /outputs/output_data.xlsx
```

#### Api service
##### Using uv
```bash
# Using module syntax
uv run python -m cli.run_api --host 0.0.0.0 --port 8000 --log-level warning

# Using installed command
uv run invoice-api --host 0.0.0.0 --port 8000 --log-level warning
```

##### Using docker

```bash
docker compose build && docker compose up -d
```

