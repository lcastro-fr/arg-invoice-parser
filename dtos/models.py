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
      letra: str | None = None #!TODO Validar letra contra tipo de comprobante, o inferir desde tipo_cmp
      orden_compra: str | None = None
      qr_decoded: bool = Field(default=False)
      check: bool = Field(default=False)

      @model_validator(mode='after')
      def validate_importes(self):
          if self.importe_neto is None or self.importe_bruto is None:
              self.check = False
              return self

          # importe neto no puede ser mayor al bruto
          if self.importe_neto > self.importe_bruto:
              self.check = False
              return self

          # importe neto + impuestos no puede ser mucho mayor al bruto
          tolerancia = 1.32
          if self.importe_neto * tolerancia < self.importe_bruto:
              self.check = False
              return self

          self.check = True
          return self
      