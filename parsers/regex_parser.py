import re
from datetime import datetime
import statistics
import logging

logger = logging.getLogger(__name__)


class RegexParser:
    """
    Consideraciones:
    - Referencia: formato 0000-00000000
    - Fecha: dd/mm/yyyy o dd-mm-yy. Es la primera que aparece en el doc
    - CUIT: XX-XXXXXXXX-X o XXXXXXXXXXX (11 dígitos)
    - Importe Bruto: el mayor de los importes encontrados
    - Importe Neto: el inmediatamente inferior al bruto
    - Moneda: por ahora siempre ARS
    - TipoCmp: código numérico (006, 011) en el encabezado (primeras 5 filas)
    - Letra: A, B, C en el encabezado (primeras 5 filas)
    """

    CUIT_FR = "30540080298"

    def __init__(self, raw_text):
        self.text = raw_text
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

    def _extract_referencia(self):
        ref_regex = r"\b\d{4,5}\s?-\s?\d{8}\b"
        ref_matches = re.findall(ref_regex, self.text)
        if ref_matches:
            return ref_matches[0].replace(" ", "")
        return None

    def _extract_fecha(self):
        date_regex = r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"
        date_matches = re.findall(date_regex, self.text)
        if date_matches:
            # La fecha de emisión es la primera del documento
            try:
                date_str = date_matches[0].replace("-", "/")
                dt_obj = datetime.strptime(date_str, "%d/%m/%Y")
                return dt_obj.strftime("%Y-%m-%d")
            except Exception:
                return date_matches[0]  # Fallback si falla el parseo

    def _extract_cuit(self):
        cuit_regex = r"\b(?:20|23|27|30|33)(?:-?\d{8}-?\d)\b"
        cuit_matches = [c.replace("-", "") for c in re.findall(cuit_regex, self.text)]
        cuit_matches = [c for c in cuit_matches if c != self.CUIT_FR]
        if cuit_matches:
            return cuit_matches[0]
        return None

    def extract_importes(self):
        """Extrae importes con coma y punto como separador.
        - El importe bruto deberia ser el mas grande de todos.
        - El importe neto deberia ser el inmediamente inferior al bruto.
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

        # Eliminados duplicados y ordenamos
        unique_amounts = sorted(list(set(found_amounts)), reverse=True)
        results = {
            "importe_bruto": None,
            "importe_neto": None,
            "debug": {"candidatos_encontrados": unique_amounts[:5]},  # Debug
        }

        if not unique_amounts:
            return results

        if len(unique_amounts) > 3:
            # Calculamos la mediana para descargar importes muy dispersos
            median = statistics.median(unique_amounts[:5])
            upper = 20.0  # 20 veces mayor
            lower = 0.05  # 20 veces menor
            filtered_amounts = [
                amt
                for amt in unique_amounts
                if (median * lower) <= amt <= (median * upper)
            ]
            unique_amounts = sorted(filtered_amounts, reverse=True)
            results["debug"]["median"] = median  # Debug
            results["debug"]["filtered_candidatos"] = unique_amounts

        results["importe_bruto"] = unique_amounts[0]  # El mayor es el bruto

        if len(unique_amounts) > 1:
            results["importe_neto"] = unique_amounts[1]
        else:
            results["importe_neto"] = unique_amounts[0]

        return results

    def _extract_tipo_cmp(self):
        header_text = " ".join(self.lines[:5])
        cod_regex = r"\b\d{1,3}\b"
        cod_matches = re.findall(cod_regex, header_text)

        for num in cod_matches:
            if len(num) == 3 or (len(num) == 2 and num.startswith("0")):
                return int(num)
        return None

    def extract_letra(self):
        header_text = " ".join(self.lines[:5])
        letter_regex = r"\b[ABCEM]\b"
        letter_matches = re.findall(letter_regex, header_text)

        for letra in letter_matches:
            return letra
        return None

    def extract_oc(self):
        oc_regex = r"\b(?:46|52)\d{8}\b"  # TODO Ver si hay mas numeraciones, eg 46, 52
        oc_matches = re.findall(oc_regex, self.text)
        if oc_matches:
            return oc_matches[0]
        return None

    def extract_data(self):
        data = {
            "referencia": None,
            "fecha": None,
            "cuit": None,
            "importe_bruto": None,
            "importe_neto": None,
            "moneda": "ARS",  # TODO Detectar moneda. Hardcodeado por ahora
            "tipoCmp": None,  # Código numérico (006, 011)
            "letra": None,  # Letra (A, B, C)
            "orden_compra": None,
        }

        try:
            # 1. REFERENCIA (formato 0000-00000000)
            data["referencia"] = self._extract_referencia()
        except Exception as e:
            logger.error(f"Error extracting referencia: {e}")

        try:
            # 2. FECHA (dd/mm/yyyy o dd-mm-yy)
            data["fecha"] = self._extract_fecha()
        except Exception as e:
            logger.error(f"Error extracting fecha: {e}")

        try:
            # 3. CUIT (XX-XXXXXXXX-X o XXXXXXXXXXX)
            data["cuit"] = self._extract_cuit()
        except Exception as e:
            logger.error(f"Error extracting cuit: {e}")

        try:
            # 4 & 5. IMPORTES (Bruto y Neto)
            importes = self.extract_importes()
            data["importe_bruto"] = importes["importe_bruto"]
            data["importe_neto"] = importes["importe_neto"]
            data["debug"] = importes.get("debug", {})
        except Exception as e:
            logger.error(f"Error extracting importes: {e}")

        try:
            # 6 & 7. ENCABEZADO (Primeras 5 líneas)
            data["tipoCmp"] = self._extract_tipo_cmp()
            data["letra"] = self.extract_letra()
        except Exception as e:
            logger.error(f"Error extracting tipoCmp/letra: {e}")

        try:
            # 8. ORDEN DE COMPRA
            data["orden_compra"] = self.extract_oc()
        except Exception as e:
            logger.error(f"Error extracting orden_compra: {e}")

        return data


if __name__ == "__main__":
    sample_text = """
        Extracted Text:  ORIGINAL
        Insumos DIB SRL A FACTURA
        San Lorenzo 2971 - B1651AMI - San Andrés
        Cod.Nº 01 Nº 0003-00062123
        Prov: Buenos Aires
        Tel-Fax 4713-4768 / 6929 Fecha: 27-06-25
        e-mail: ventas@insumosdib.com.ar
        www.insumosdib.com.ar C.U.I.T.30-70880171-9
        Ing. Brutos C.M.902-820086-4
        IVA RESPONSABLE INSCRIPTO
        Inicio Actividades:07/06/2004
        SR/ES: FRIGORIFICO RIOPLATENSE SAICIF - (05781) PD Vendedor: ..
        Domicilio: AV DE LOS CONSTITUYENTES 2499 - GENERAL PACHECO Cond.Pago: ANTICIPO TRANSFERENCIA
        1617 - - BUENOS AIRES Remitos: 0001-00077359
        Telefonos: 4006 2500
        Cond. IVA: Resp. Inscripto C.U.I.T.:30-54008029-8 Ord.Compra: --4600088530
        E-Mail: SGUERRA@RIOPLATENSE.COM
        It. Artículo Cantidad Descripción Despacho P.Unitario Total item
        1 ARMF121C2 1 URANGA Man. HSS MACHO M.Fina 12.0 X 1.00 - C2 51,000.78 51,000.78
        2 ARMF181C2 1 URANGA Man. HSS MACHO M.Fina 18.0 X 1.00 - C2 89,645.57 89,645.57
        3 ARMF3015C2 1 URANGA Man. HSS MACHO M.Fina 30.0 X 1.50 - C2 247,227.26 247,227.26
        27-06-25 14:34 SON PESOS: Cuatrocientos Setenta Mil Cuatrocientos Noventa Con Sesenta Subtotal 387,873.61
        y Nueve Centavos
        IMPORTANTE
        Cotización U$D: 1189.50 IVA Ins: 21.00% 81,453.46
        Facturado en PESOS Según TC vendedor BNA día anterior. Perc.IB: 0.30% 1,163.62
        Se emitirá NC/ND según variaciones del DOLAR al momento efectivo pago
        CAE Nº: 75269276810625
        TOTAL $ 470,490.69
        Fecha Venc. CAE:07-07-25
        Comprobante Autorizado
        Cheques a la orden de Insumos DIB s.r.l. - NO SE ACEPTAN CHEQUES DE TERCEROS
        """
    parser = RegexParser(sample_text)
    extracted_data = parser.extract_data()
    print(extracted_data)
