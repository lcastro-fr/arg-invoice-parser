import re
from datetime import datetime
import statistics
import logging
from dtos import InvoiceData, ImportesResult, ImportesDebugInfo

logger = logging.getLogger(__name__)


class RegexParser:
    """
    Considerations:
    - Reference: format 0000-00000000 or pto_venta - numero in the header (first 10 lines)
    - Date: dd/mm/yyyy,dd-mm-yy, dd.mm.yyyy, etc. It is the first one that appears in the doc
    - CUIT: XX-XXXXXXXX-X or XXXXXXXXXXX <> CUIT_FR (11 digits)
    - Gross Amount: the largest of the amounts found
    - Net Amount: immediately below the gross amount
    - Currency: currently always ARS
    - TipoCmp: numeric code (006, 011, etc.) in the header (first 10 lines). Valid AFIP ranges
    - Letter: A, B, C in the header (first 10 lines)
    """

    def __init__(
        self, raw_text: str, own_cuit: str | None = None, verbose: bool = False
    ):
        self.text = raw_text
        self.own_cuit = own_cuit
        self.invoice_data = InvoiceData()
        self.lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    def _parse_arg_float(self, num_str):
        try:
            last_dot = num_str.rfind(".")
            last_comma = num_str.rfind(",")

            if last_dot > last_comma:
                # es "."
                num_str = num_str.replace(",", "")
            elif last_comma > last_dot:
                # es ","
                num_str = num_str.replace(".", "").replace(",", ".")

            return float(num_str)
        except ValueError:
            return 0.0

    def _format_referencia(self, referencia):
        if "-" not in referencia:
            num = referencia[:-8]
            pto_venta = referencia[len(referencia) - 8 :]
            return f"{num}-{pto_venta}"
        return referencia

    def _extract_referencia(self) -> str | None:
        # Should be in the header
        ref_regex = r"\b\d{4,5}\s?-?\s?\d{8}\b"
        header_text = " ".join(self.lines[:10])
        ref_matches = re.findall(ref_regex, header_text)
        if ref_matches:
            return self._format_referencia(ref_matches[0].replace(" ", ""))

        # Try to find pto_venta and numero separately
        pto_venta_regex = r"(?<![.\d/-])\d{4,5}(?![.\d/-])"
        numero_regex = r"(?<![.\d/-])\d{8}(?![.\d/-])"
        pto_venta_matches = re.findall(pto_venta_regex, header_text)
        numero_matches = re.findall(numero_regex, header_text)
        if pto_venta_matches and numero_matches:
            return f"{pto_venta_matches[0]}-{numero_matches[0]}"

        return None

    def _extract_fecha(self) -> str | None:
        date_regex = r"\b(\d{1,2}([-\.\/\s])\d{1,2}\2\d{2,4})\b"
        date_matches = re.findall(date_regex, self.text)
        if date_matches:
            # The issue date is the first one in the document
            for full_date, separator in date_matches:
                try:
                    date_str = full_date.replace(separator, "/")
                    split_dates = date_str.split("/")
                    day, month, year = split_dates
                    if len(year) == 2:
                        year = "20" + year
                    dt_obj = datetime(int(year), int(month), int(day))

                    current_year = datetime.now().year
                    if not current_year - 10 <= dt_obj.year <= current_year + 1:
                        continue  # Skip unrealistic years

                    # Return the first valid date found
                    return dt_obj.strftime("%Y-%m-%d")
                except Exception:
                    pass

    def _extract_cuit(self) -> str | None:
        cuit_regex = r"\b(?:20|23|27|30|33)(?:-?\d{8}-?\d)\b"
        for line in self.lines[:10]:  # Only search in the header (first 10 lines)
            matches = re.findall(cuit_regex, line)
            for match in matches:
                cuit = match.replace("-", "")
                if cuit != self.own_cuit:
                    return cuit
        return None

    def extract_importes(self) -> ImportesResult:
        """Extract amounts with comma and dot as separators.
        - The gross amount should be the largest of all.
        - The net amount should be immediately below the gross.
        """
        found_amounts = []
        regex_arg = r"\b(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}\b"
        matches_arg = re.findall(regex_arg, self.text)

        for m in matches_arg:
            val_str = m.replace(".", "").replace(",", ".")
            try:
                val = float(val_str)
                found_amounts.append(val)
            except ValueError:
                continue

        regex_us = r"\b(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}\b"
        matches_us = re.findall(regex_us, self.text)
        for m in matches_us:
            val_str = m.replace(",", "")
            try:
                val = float(val_str)
                found_amounts.append(val)
            except ValueError:
                continue

        # Remove duplicates and very close amounts
        unique_amounts = []
        for amt in sorted(found_amounts, reverse=True):
            # Check if the amount is very close to any already added. Sometimes they duplicate with a decimal difference
            if not any(abs(existing - amt) < 1 for existing in unique_amounts):
                unique_amounts.append(amt)

        debug_info = ImportesDebugInfo(candidatos_encontrados=unique_amounts[:5])
        result = ImportesResult(debug=debug_info)

        if not unique_amounts:
            return result

        if len(unique_amounts) > 3:
            # Calculate the median to filter out very dispersed amounts
            median = statistics.median(unique_amounts[:5])
            upper = 20.0  # 20 times higher
            lower = 0.05  # 20 times lower
            filtered_amounts = [
                amt
                for amt in unique_amounts
                if (median * lower) <= amt <= (median * upper)
            ]
            unique_amounts = sorted(filtered_amounts, reverse=True)
            result.debug.median = median
            result.debug.filtered_candidatos = unique_amounts

        result.importe_bruto = unique_amounts[0]  # The largest is the gross amount

        if len(unique_amounts) > 1:
            result.importe_neto = unique_amounts[1]
        else:
            result.importe_neto = unique_amounts[0]

        return result

    def _extract_tipo_cmp(self):
        header_text = " ".join(self.lines[:10])
        cod_regex = r"(?<![.\d/-])\d{1,3}(?![.\d/-])"
        cod_matches = re.findall(cod_regex, header_text)

        # Valid AFIP ranges
        for num in cod_matches:
            tmp = int(num)
            if tmp <= 9:
                return tmp

            if tmp <= 99:
                if 10 <= tmp <= 66 or tmp in (81, 82, 83, 88, 89, 90, 91, 99):
                    return tmp

            if tmp <= 999:
                if (
                    101 <= tmp <= 117
                    or tmp in (183, 186, 190)  # Hacienda
                    or 201 <= tmp <= 213
                    or tmp in (331, 332)
                    or 991 <= tmp <= 998
                ):
                    return tmp
        return None

    def extract_letra(self):
        header_text = " ".join(self.lines[:10])
        letter_regex = r"\b(?<![.\d/-])[ABCEM](?![.\d/-])\b"
        letter_matches = re.findall(letter_regex, header_text)

        for letra in letter_matches:
            return letra
        return None

    def extract_oc(self):
        oc_regex = (
            r"\b(?:46|52)\d{8}\b"  # TODO See if there are more numberings, e.g. 46, 52
        )
        oc_matches = re.findall(oc_regex, self.text)
        if oc_matches:
            return oc_matches[0]
        return None

    def extract_data(self) -> InvoiceData:
        try:
            # 1. REFERENCE (format 0000-00000000)
            self.invoice_data.referencia = self._extract_referencia()
        except Exception as e:
            logger.error(f"Error obtaining reference: {e}")

        try:
            # 2. DATE (dd/mm/yyyy or dd-mm-yy)
            self.invoice_data.fecha = self._extract_fecha()
        except Exception as e:
            logger.error(f"Error obtaining date: {e}")

        try:
            # 3. CUIT (XX-XXXXXXXX-X o XXXXXXXXXXX)
            self.invoice_data.cuit = self._extract_cuit()
        except Exception as e:
            logger.error(f"Error obtaining cuit: {e}")

        try:
            # 4 & 5. AMOUNTS (Gross and Net)
            importes = self.extract_importes()
            self.invoice_data.importe_bruto = importes.importe_bruto
            self.invoice_data.importe_neto = importes.importe_neto
        except Exception as e:
            logger.error(f"Error obtaining amounts: {e}")

        try:
            # 6 & 7. HEADER (First 10 lines)
            self.invoice_data.tipo_cmp = self._extract_tipo_cmp()
            self.invoice_data.letra = self.extract_letra()
        except Exception as e:
            logger.error(f"Error obtaining tipoCmp/letra: {e}")

        try:
            # 8. PURCHASE ORDER
            self.invoice_data.orden_compra = self.extract_oc()
        except Exception as e:
            logger.error(f"Error obtaining purchase order: {e}")

        self.invoice_data.qr_decoded = False
        return self.invoice_data
