from pydantic import BaseModel, Field, model_validator


class ImportesDebugInfo(BaseModel):
    candidatos_encontrados: list[float] = Field(default_factory=list)
    median: float | None = None
    filtered_candidatos: list[float] | None = None


class ImportesResult(BaseModel):
    importe_bruto: float | None = None
    importe_neto: float | None = None
    debug: ImportesDebugInfo = Field(default_factory=ImportesDebugInfo)


class InvoiceData(BaseModel):
    referencia: str | None = None
    fecha: str | None = None
    cuit: str | None = None
    importe_bruto: float | None = None
    importe_neto: float | None = None
    moneda: str = "ARS"
    tipo_cmp: int | None = None
    letra: str | None = None  #!TODO Validate if letra can be inferred from tipo_cmp
    orden_compra: str | None = None
    qr_decoded: bool = Field(default=False)
    check: bool = Field(default=False)

    def _check_amounts(self):
        if self.importe_neto is None or self.importe_bruto is None:
            return False

        # net amount cannot be greater than gross amount
        if self.importe_neto > self.importe_bruto:
            return False

        # net amount + tax should be approximately equal to gross amount
        tolerancia = 1.32
        if self.importe_neto * tolerancia < self.importe_bruto:
            return False

        return True

    @model_validator(mode="after")
    def validate_check(self):
        if (
            any(
                field is None
                for field in [
                    self.referencia,
                    self.fecha,
                    self.cuit,
                    self.importe_bruto,
                    self.importe_neto,
                    self.letra,
                    self.tipo_cmp,
                ]
            )
            or not self._check_amounts()
        ):
            self.check = False
        return self
