from pydantic import BaseModel
from dtos import InvoiceData


class InvoiceParseResponse(BaseModel):
    success: bool
    data: InvoiceData | None = None
    error_message: str | None = None
