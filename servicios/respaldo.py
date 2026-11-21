"""
respaldo.py
Copia de seguridad con un botón (RF12): base de datos + escaneados + plantillas
en un solo archivo .zip.
"""

import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from database import CARPETA_SISTEMA, RUTA_BD

CARPETA_RESPALDOS = CARPETA_SISTEMA / "respaldos"
CARPETAS_A_COPIAR = ("archivos", "plantillas")


def crear_respaldo(carpeta_destino=None):
    """
    Crea respaldo_AAAA-MM-DD_HH-MM.zip y devuelve su ruta.
    carpeta_destino: por ejemplo una memoria USB. Si no se indica,
    se guarda en la carpeta 'respaldos' del sistema.
    """
    destino = Path(carpeta_destino) if carpeta_destino else CARPETA_RESPALDOS
    destino.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ruta_zip = destino / f"respaldo_{marca}.zip"

    with tempfile.TemporaryDirectory() as temporal:
        # Copia segura de la base: SQLite la copia aunque el programa esté abierto.
        copia_bd = Path(temporal) / "direccion.db"
        origen = sqlite3.connect(RUTA_BD)
        copia = sqlite3.connect(copia_bd)
        with copia:
            origen.backup(copia)
        origen.close()
        copia.close()

        with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as archivo_zip:
            archivo_zip.write(copia_bd, "direccion.db")
            for nombre in CARPETAS_A_COPIAR:
                carpeta = CARPETA_SISTEMA / nombre
                if not carpeta.exists():
                    continue
                for ruta in carpeta.rglob("*"):
                    if ruta.is_file():
                        archivo_zip.write(ruta, ruta.relative_to(CARPETA_SISTEMA).as_posix())
    return ruta_zip
