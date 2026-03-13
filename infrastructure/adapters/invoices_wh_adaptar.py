import logging

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from dtos.models import InvoiceData
from infrastructure.models.invoice_model import InvoiceModel
from infrastructure.ports.invoices_wh_port import InvoicesWHPort

logger = logging.getLogger(__name__)


class InvoicesWHAdapter(InvoicesWHPort):
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def get_invoice(self, referencia: str, cuit: str, letra: str) -> InvoiceData | None:
        try:
            reference = referencia.replace("-", letra)
            with Session(self.engine) as session:
                stmt = select(InvoiceModel).where(
                    InvoiceModel.referencia == reference,
                    InvoiceModel.cuit == cuit,
                )
                row = session.execute(stmt).scalar_one_or_none()
                if row is None:
                    return None

                match row.moneda:
                    case "$":
                        moneda = "ARS"
                    case "€":
                        moneda = "EUR"
                    case _:
                        moneda = row.moneda or "ARS"

                referencia = (
                    row.referencia.replace(row.letra, "-")
                    if row.letra
                    else row.referencia
                )

                return InvoiceData(
                    referencia=referencia,
                    fecha=row.fecha.strftime("%Y-%m-%d") if row.fecha else None,
                    cuit=row.cuit,
                    importe_bruto=row.importe_bruto,
                    importe_neto=row.importe_neto,
                    moneda=moneda,
                    tipo_cmp=row.tipo_cmp,
                    letra=row.letra,
                    db_retrieved=True,
                )
        except Exception as e:
            logger.warning(
                f"Database query failed for referencia={referencia}, cuit={cuit}: {e}"
            )
            return None
