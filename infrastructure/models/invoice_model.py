from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class InvoiceModel(Base):
    __tablename__ = "facturas_afip"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referencia: Mapped[str | None] = mapped_column(String, index=True)
    cuit: Mapped[str | None] = mapped_column(String, index=True)
    fecha: Mapped[Date | None] = mapped_column(Date)
    importe_bruto: Mapped[float | None] = mapped_column("imp_total", Float)
    importe_neto: Mapped[float | None] = mapped_column("imp_neto_grav", Float)
    moneda: Mapped[str | None] = mapped_column(String)
    tipo_cmp: Mapped[int | None] = mapped_column("clase_doc", Integer)
    letra: Mapped[str | None] = mapped_column("letra_doc", String)
