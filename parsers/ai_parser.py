import ollama
import logging

TEXT_MODEL = "qwen2.5"

PROMPT_TEMPLATE = """
### ROLE
You are an expert data extraction assistant for Argentine financial documents (AFIP).
Your goal is to parse raw OCR text from invoices and return a strictly formatted JSON object.


### TARGET FIELDS DEFINITION
Extract these fields from the text below. If a field is not found, return null.

1. "fecha": The main invoice date. Convert to ISO format "YYYY-MM-DD".
   - Look for "Fecha de Emision", "Fecha", or dates like "DD/MM/YYYY" or "DD-MM-YY".
2. "cuit": The issuer's Tax ID. 
   - Extract only the 11 digits (remove dashes/spaces).
   - Look for "CUIT", "C.U.I.T".
   - Formats: 30-12345678-9, 20123456789, etc.
3. "referencia": The full invoice number (Point of Sale + ID).
   - Format: "XXXX-XXXXXXXX" (e.g., 0003-00004567).
   - Look for "Comp. Nro", "Factura Nro", "Nº",  or patterns like 0001-00000001.
4. "importe_bruto": The final TOTAL amount including taxes.
   - Look for "Total", "Total a Pagar", "Importe Total".
   - **Format:** The input uses comma (,) as decimal separator (e.g. 1.500,00 = 1500.00). Return a JSON Number (float).
5. "importe_neto": The taxable amount BEFORE taxes (Subtotal).
   - Look for "Importe Neto", "Neto Gravado", "Subtotal".
   - If multiple subtotals exist, sum them or pick the main one.
6. "moneda": Currency. "ARS" (Pesos) or "USD" (Dollars). Default to "ARS" if symbol is "$" or missing.
7. "tipoCmp": The numeric AFIP Document Code.
   - Look for "Cod.", "Codigo", "Cod.Nº". Examples: 001, 006, 011, 051.
   - Return as an Integer (e.g., 6).
8. "tipoCodAut": The Invoice Letter/Class.
   - Examples: "A", "B", "C", "M".
   - Usually found in a box with the text "Factura" or just the big letter itself.

### RAW TEXT INPUT
{raw_text}

### RESPONSE
Output ONLY the valid JSON object. Do not explain your reasoning.
"""

logger = logging.getLogger(__name__)


class AIParser:
    def __init__(
        self,
        text_content,
        model="qwen2.5",
        host="http://172.20.160.1:11434",
        chat_args={},
        client_args={},
    ):
        self.text_content = text_content
        self.model = model
        self.host = host
        self.chat_args = chat_args
        self.client_args = client_args

    def parse(self):
        try:
            client = ollama.Client(host=self.host, **self.client_args)
            response = client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": PROMPT_TEMPLATE.format(raw_text=self.text_content),
                    }
                ],
                format="json",
                **self.chat_args,
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Error during AI parsing: {e}")
            return
