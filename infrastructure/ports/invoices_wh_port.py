from abc import ABC, abstractmethod

from dtos.models import InvoiceData


class InvoicesWHPort(ABC):
    @abstractmethod
    def get_invoice(self, referencia: str, cuit: str, letra: str) -> InvoiceData | None:
        pass
