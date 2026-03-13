import logging
from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile

from use_cases import ParseInvoiceUseCase

from .dtos import InvoiceParseResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    invoices_wh_port = ParseInvoiceUseCase._create_adapter_from_env()
    if invoices_wh_port:
        logger.info("Database adapter initialized successfully")
    app.state.parse_invoice_use_case = ParseInvoiceUseCase(
        invoices_wh_port=invoices_wh_port
    )
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "ok"}


@app.post("/invoice/parse", status_code=200)
async def parse_invoice(
    request: Request,
    file: UploadFile = File(...),
    cuit: str | None = Form(None),
) -> InvoiceParseResponse:
    try:
        file_content = await file.read()
        file_bytes_io = BytesIO(file_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {e}")

    try:
        use_case: ParseInvoiceUseCase = request.app.state.parse_invoice_use_case
        invoice_data = use_case.parse_invoice(file_bytes_io, own_cuit=cuit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing invoice: {e}")

    if not invoice_data:
        return InvoiceParseResponse(
            success=False, data=None, error_message="No data extracted from invoice."
        )

    return InvoiceParseResponse(success=True, data=invoice_data)
