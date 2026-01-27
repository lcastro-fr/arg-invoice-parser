from parsers import RegexParser

CUIT_FR = "30540080298"


def test_extract_referencia():
    sample_text = "Factura A 0001-00001234\nOtra línea"
    parser = RegexParser(sample_text)
    referencia = parser._extract_referencia()
    assert referencia == "0001-00001234"

    with_spaces = "Factura A  0002 - 00005678\nOtra línea"
    parser = RegexParser(with_spaces, own_cuit=CUIT_FR)
    referencia = parser._extract_referencia()
    assert referencia == "0002-00005678"

    sample_text = """
        Q Gráfica Ideal FACTURA
        COD. 01
        Fecha 05.06.2025
        Punto de Venta: 00001 Comp. Nro: 00000301
        IMPRESIONES EN GENERAL
        Fecha de Emisión: 11/07/2025
        Razón Social: ChlARRA ERNESTO OSCAR
        Domicilio Comercial: Montes De Oca 6797 - Munro, Buenos Aires CUIT: 20161247953
        Ingresos Brutos: 20161247953
        """
    parser = RegexParser(sample_text, own_cuit=CUIT_FR)
    referencia = parser._extract_referencia()
    assert referencia == "00001-00000301"


def test_extract_cuit():
    sample_text = "CUIT: 20-12345678-9\nOtra línea"
    parser = RegexParser(sample_text, own_cuit=CUIT_FR)
    cuit = parser._extract_cuit()
    assert cuit == "20123456789"

    without_dashes = "CUIT: 27123456789\nOtra línea"
    parser = RegexParser(without_dashes, own_cuit=CUIT_FR)
    cuit = parser._extract_cuit()
    assert cuit == "27123456789"


def test_extract_fecha():
    sample_text = "Fecha: 15/08/2023\nOtra línea"
    parser = RegexParser(sample_text, own_cuit=CUIT_FR)
    fecha = parser._extract_fecha()
    assert fecha == "2023-08-15"

    with_dashes = "Fecha: 01-01-22\nOtra línea"
    parser = RegexParser(with_dashes, own_cuit=CUIT_FR)
    fecha = parser._extract_fecha()
    assert fecha == "2022-01-01"

    with_dashes_full_year = "Fecha: 05-12-2021\nOtra línea"
    parser = RegexParser(with_dashes_full_year, own_cuit=CUIT_FR)
    fecha = parser._extract_fecha()
    assert fecha == "2021-12-05"

    with_dots = "Fecha: 23.03.2020\nOtra línea"
    parser = RegexParser(with_dots, own_cuit=CUIT_FR)
    fecha = parser._extract_fecha()
    assert fecha == "2020-03-23"


def test_extract_oc():
    sample_text = "Orden de Compra: 4612345678\nOtra línea"
    parser = RegexParser(sample_text, own_cuit=CUIT_FR)
    oc = parser.extract_oc()
    assert oc == "4612345678"

    no_oc = "No hay orden de compra aquí.\nOtra línea"
    parser = RegexParser(no_oc, own_cuit=CUIT_FR)
    oc = parser.extract_oc()
    assert oc is None


def test_extract_letra():
    sample_text = "Factura A 0001-00001234\nOtra línea"
    parser = RegexParser(sample_text, own_cuit=CUIT_FR)
    letra = parser.extract_letra()
    assert letra == "A"

    no_letra = "Factura 0001-00001234\nOtra línea"
    parser = RegexParser(no_letra, own_cuit=CUIT_FR)
    letra = parser.extract_letra()
    assert letra is None


def test_extract_tipo_cmp():
    sample_text = "Tipo de Comprobante: 01\nOtra línea"
    parser = RegexParser(sample_text, own_cuit=CUIT_FR)
    tipo_cmp = parser._extract_tipo_cmp()
    assert tipo_cmp == 1

    another_type = "Tipo de Comprobante: 101\nOtra línea"
    parser = RegexParser(another_type, own_cuit=CUIT_FR)
    tipo_cmp = parser._extract_tipo_cmp()
    assert tipo_cmp == 101

    sample_text = """
        ORIGINAL
        N° 0009-00015078
        A
        Fecha 08.04.2025
        Sealed Air Argentina S.A.
        Documento Interno 492366433
        Primera Junta 550
        Código No. 201
        B1878IPL Quilmes C.U.I.T. : 30-50104769-0
        """
    parser = RegexParser(sample_text, own_cuit=CUIT_FR)
    tipo_cmp = parser._extract_tipo_cmp()
    assert tipo_cmp == 201

    no_type = "No hay tipo de comprobante aquí.\nOtra línea"
    parser = RegexParser(no_type, own_cuit=CUIT_FR)
    tipo_cmp = parser._extract_tipo_cmp()
    assert tipo_cmp is None


def test_extract_importes():
    sample_text = """1 ARMF121C2 1 URANGA Man. HSS MACHO M.Fina 12.0 X 1.00 - C2 51,000.78 51,000.78
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
        Cheques a la orden de Insumos DIB s.r.l. - NO SE ACEPTAN CHEQUES DE TERCEROS"""
    parser = RegexParser(sample_text, own_cuit=CUIT_FR)
    importes = parser.extract_importes()
    assert importes.importe_neto == 387873.61
    assert importes.importe_bruto == 470490.69
