"""
utilidades.py
Funciones de apoyo: fechas, nombres de archivo y abrir archivos.
"""

import os
import re
import subprocess
import sys
from datetime import datetime

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def fecha_a_iso(texto):
    """'21/09/2026' -> '2026-09-21' (como se guarda en la base de datos)."""
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"La fecha '{texto}' no es válida. Use el formato dd/mm/aaaa.")


def iso_a_fecha(iso):
    """'2026-09-21' -> '21/09/2026' (como se muestra en pantalla)."""
    if not iso:
        return ""
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")


def fecha_hora_a_iso(texto):
    """'10/09/2026 13:05' -> '2026-09-10 13:05'."""
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y %H:%M").strftime("%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError(
            f"La fecha y hora '{texto}' no es válida. Use el formato dd/mm/aaaa hh:mm."
        )


def iso_a_fecha_hora(iso):
    """'2026-09-10 13:05' -> '10/09/2026 13:05'."""
    if not iso:
        return ""
    return datetime.strptime(iso, "%Y-%m-%d %H:%M").strftime("%d/%m/%Y %H:%M")


def hoy():
    return datetime.now().strftime("%d/%m/%Y")


def ahora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def fecha_en_letras(iso):
    """'2026-09-21' -> '21 de septiembre de 2026' (como va en el oficio)."""
    fecha = datetime.strptime(iso, "%Y-%m-%d")
    return f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


def nombre_archivo_seguro(texto, largo_maximo=80):
    """Quita los caracteres que Windows no permite en nombres de archivo."""
    limpio = re.sub(r'[\\/:*?"<>|]', "", texto)
    limpio = re.sub(r"\s+", " ", limpio).strip()
    return limpio[:largo_maximo].strip()


def texto_vacio(valor):
    return valor is None or str(valor).strip() == ""


def abrir_con_programa(ruta):
    """Abre un archivo con el programa que corresponde (Word, visor de PDF...)."""
    ruta = str(ruta)
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No se encontró el archivo:\n{ruta}")
    if sys.platform.startswith("win"):
        os.startfile(ruta)  # noqa: solo existe en Windows
    elif sys.platform == "darwin":
        subprocess.Popen(["open", ruta])
    else:
        subprocess.Popen(["xdg-open", ruta])
