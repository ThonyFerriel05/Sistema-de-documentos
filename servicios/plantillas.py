"""
plantillas.py
Llena una plantilla Word con los datos del oficio (RF13) y crea la plantilla base.

Marcas que se pueden poner en cualquier plantilla Word:
    {{FECHA}}               -> 21 de septiembre de 2026
    {{CODIGO}}              -> DIR.CARR.ING.SISTEMAS F.IN.I. OF. No. 112/2026
    {{DESTINATARIO_NOMBRE}} {{DESTINATARIO_CARGO}}
    {{VIA_NOMBRE}} {{VIA_CARGO}}   (si no hay VIA, esas líneas se borran)
    {{ASUNTO}}              -> lo que va en REF.
    {{GESTION}}             -> 2026
"""

from docx import Document as WordDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

MARCAS_VIA = ("{{VIA_NOMBRE}}", "{{VIA_CARGO}}")


def _todos_los_parrafos(documento):
    """Párrafos del cuerpo, de las tablas y del encabezado/pie de página."""
    def de_contenedor(contenedor):
        for parrafo in contenedor.paragraphs:
            yield parrafo
        for tabla in getattr(contenedor, "tables", []):
            for fila in tabla.rows:
                for celda in fila.cells:
                    yield from de_contenedor(celda)

    yield from de_contenedor(documento)
    for seccion in documento.sections:
        for parte in (seccion.header, seccion.footer):
            yield from de_contenedor(parte)


def _reemplazar_en_parrafo(parrafo, datos):
    if "{{" not in parrafo.text:
        return
    # 1) Intento normal: la marca está entera dentro de un solo tramo de texto,
    #    así se conserva el formato (negrita, subrayado...).
    for run in parrafo.runs:
        for marca, valor in datos.items():
            if marca in run.text:
                run.text = run.text.replace(marca, valor)
    # 2) Si Word partió la marca en varios tramos, se une el texto del párrafo.
    if any(marca in parrafo.text for marca in datos):
        texto = parrafo.text
        for marca, valor in datos.items():
            texto = texto.replace(marca, valor)
        runs = parrafo.runs
        runs[0].text = texto
        for run in runs[1:]:
            run.text = ""


def llenar_plantilla(ruta_plantilla, datos, ruta_salida):
    """
    datos: diccionario {"{{MARCA}}": "valor"}.
    Si la VIA viene vacía, se borran las líneas que la contienen.
    """
    documento = WordDocument(str(ruta_plantilla))
    sin_via = not datos.get("{{VIA_NOMBRE}}")

    for parrafo in list(_todos_los_parrafos(documento)):
        if sin_via and any(marca in parrafo.text for marca in MARCAS_VIA):
            elemento = parrafo._element
            elemento.getparent().remove(elemento)
            continue
        _reemplazar_en_parrafo(parrafo, datos)

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    documento.save(str(ruta_salida))
    return ruta_salida


# ---------------------------------------------------------------------------
# Plantilla base, copiada del formato real de los oficios de la dirección.
# Los logos no se incluyen: se agregan abriendo este Word una sola vez.
# ---------------------------------------------------------------------------

def _parrafo(doc, texto="", negrita=False, cursiva=False, subrayado=False,
             alineacion=None, tamano=11, sangria_cm=None, espacio_despues=0):
    p = doc.add_paragraph()
    if texto:
        run = p.add_run(texto)
        run.bold, run.italic, run.underline = negrita, cursiva, subrayado
        run.font.size = Pt(tamano)
    if alineacion is not None:
        p.alignment = alineacion
    if sangria_cm is not None:
        p.paragraph_format.left_indent = Cm(sangria_cm)
    p.paragraph_format.space_after = Pt(espacio_despues)
    return p


def _linea_persona(doc, etiqueta, marca_nombre, marca_cargo):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    etiqueta_run = p.add_run(f"{etiqueta}\t: ")
    etiqueta_run.bold = True
    p.add_run(marca_nombre)
    cargo = _parrafo(doc, sangria_cm=1.27, espacio_despues=8)
    cargo.add_run(marca_cargo).bold = True


def crear_plantilla_base(ruta):
    doc = WordDocument()
    seccion = doc.sections[0]
    seccion.page_width, seccion.page_height = Cm(21.59), Cm(27.94)  # carta
    seccion.left_margin = seccion.right_margin = Cm(2.5)
    seccion.top_margin, seccion.bottom_margin = Cm(2), Cm(2)
    doc.styles["Normal"].font.name = "Arial"
    doc.styles["Normal"].font.size = Pt(11)

    centro = WD_ALIGN_PARAGRAPH.CENTER
    derecha = WD_ALIGN_PARAGRAPH.RIGHT

    # Encabezado
    _parrafo(doc, "Universidad Autónoma “Gabriel René Moreno”", negrita=True,
             cursiva=True, alineacion=centro, tamano=14)
    _parrafo(doc, "Facultad Integral de Ichilo", cursiva=True, alineacion=centro, tamano=12)
    _parrafo(doc, "Carrera Ingeniería en Sistemas", cursiva=True, alineacion=centro,
             tamano=12, espacio_despues=18)

    # Lugar, fecha y código
    lugar = _parrafo(doc, alineacion=derecha)
    lugar.add_run("Yapacaní, ")
    lugar.add_run("{{FECHA}}")
    codigo = _parrafo(doc, alineacion=derecha, espacio_despues=18)
    codigo.add_run("{{CODIGO}}").bold = True

    # A, VIA, DE
    _linea_persona(doc, "A", "{{DESTINATARIO_NOMBRE}}", "{{DESTINATARIO_CARGO}}")
    _linea_persona(doc, "VIA", "{{VIA_NOMBRE}}", "{{VIA_CARGO}}")
    _linea_persona(doc, "DE", "M.Sc. Alicia Serrano Rodríguez",
                   "DIRECTORA DE LA CARRERA ING. EN SISTEMAS F.IN.I. – U.A.G.R.M.")

    # Referencia
    ref = _parrafo(doc, alineacion=centro, espacio_despues=12)
    ref.add_run("REF.: ").bold = True
    asunto = ref.add_run("{{ASUNTO}}")
    asunto.bold, asunto.underline = True, True

    # Cuerpo (la directora lo completa en Word)
    _parrafo(doc, "Distinguido(a):", espacio_despues=8)
    _parrafo(doc, "Mediante la presente, ", espacio_despues=8)
    _parrafo(doc, "[Escriba aquí el contenido del oficio.]", espacio_despues=8)
    _parrafo(doc, "Sin otro particular, me despido con las consideraciones más distinguidas.")
    _parrafo(doc, "Atentamente,", espacio_despues=60)

    # Firma
    _parrafo(doc, "M.Sc. Ing. Alicia Serrano Rodríguez", alineacion=centro)
    _parrafo(doc, "DIRECTORA", negrita=True, alineacion=centro)
    _parrafo(doc, "CARRERA ING. EN SISTEMAS", alineacion=centro)
    _parrafo(doc, "Facultad Integral de Ichilo - U.A.G.R.M.", alineacion=centro,
             tamano=9, espacio_despues=24)

    cc = _parrafo(doc, tamano=9)
    cc.add_run("c.c. Archivo ").font.size = Pt(9)
    cc.add_run("{{GESTION}}").font.size = Pt(9)
    cc.add_run(".").font.size = Pt(9)

    ruta.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(ruta))
    return ruta
