from fastapi import FastAPI, File, UploadFile, HTTPException
from use_cases import ParseInvoiceUseCase
from io import BytesIO
from .dtos import InvoiceParseResponse

app = FastAPI()


@app.post("/invoice/parse", status_code=200)
async def parse_invoice(
    file: UploadFile = File(...)
) -> InvoiceParseResponse:
    try:
        file_content = await file.read()
        file_bytes_io = BytesIO(file_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {e}")

    try:
        invoice_data = ParseInvoiceUseCase.parse_invoice(file_bytes_io)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing invoice: {e}")

    if not invoice_data:
        return InvoiceParseResponse(
            success=False, data=None, error_message="No data extracted from invoice."
        )

    return InvoiceParseResponse(success=True, data=invoice_data)
