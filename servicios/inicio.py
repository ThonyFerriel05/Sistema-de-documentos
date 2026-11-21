"""
inicio.py
Prepara todo la primera vez que se abre el sistema.
"""

import shutil
import sqlite3

from database import CARPETA_PROGRAMA, CARPETA_SISTEMA, RUTA_BD, crear_tablas
from modelos.tipo_tramite import CARPETA_PLANTILLAS, TipoTramite
from servicios.plantillas import crear_plantilla_base

NOMBRE_TRAMITE_BASE = "Oficio general"


# Lo que antes se guardaba dentro de la carpeta del programa.
DATOS_VIEJOS = ("archivos", "respaldos", "ultimo_respaldo.txt")


def pasar_datos_viejos():
    """
    Hasta el 21/11 los datos se guardaban en la carpeta del programa.
    Si la carpeta de Documentos todavía no tiene base de datos y la vieja sí,
    se COPIAN (los originales no se borran).
    """
    base_vieja = CARPETA_PROGRAMA / "direccion.db"
    if CARPETA_PROGRAMA.resolve() == CARPETA_SISTEMA.resolve():
        return False
    if RUTA_BD.exists() or not base_vieja.exists():
        return False
    origen, destino = sqlite3.connect(base_vieja), sqlite3.connect(RUTA_BD)
    with destino:
        origen.backup(destino)
    origen.close()
    destino.close()
    for nombre in DATOS_VIEJOS:
        viejo, nuevo = CARPETA_PROGRAMA / nombre, CARPETA_SISTEMA / nombre
        if viejo.is_dir():
            shutil.copytree(viejo, nuevo, dirs_exist_ok=True)
        elif viejo.is_file():
            shutil.copy2(viejo, nuevo)
    return True


def copiar_plantillas_incluidas():
    """Las plantillas que vienen con el programa se copian a Documentos si faltan.
    Nunca se pisa una plantilla que la directora ya modificó."""
    origen = CARPETA_PROGRAMA / "plantillas"
    if not origen.is_dir() or origen.resolve() == CARPETA_PLANTILLAS.resolve():
        return
    CARPETA_PLANTILLAS.mkdir(parents=True, exist_ok=True)
    for plantilla in origen.glob("*.docx"):
        destino = CARPETA_PLANTILLAS / plantilla.name
        if not destino.exists() and not plantilla.name.startswith("~$"):
            shutil.copy2(plantilla, destino)


def preparar_sistema():
    pasar_datos_viejos()
    copiar_plantillas_incluidas()
    crear_tablas()
    # Si no hay ningún trámite (primera vez), se registran las plantillas de la carpeta.
    if not TipoTramite.listar():
        ruta = CARPETA_PLANTILLAS / f"{NOMBRE_TRAMITE_BASE}.docx"
        if not ruta.exists():
            crear_plantilla_base(ruta)
        TipoTramite.crear(NOMBRE_TRAMITE_BASE, ruta)
        # Las demás plantillas que vienen con el programa (ej.: Remito de actas de graduación).
        for otra in sorted(CARPETA_PLANTILLAS.glob("*.docx")):
            if otra.stem != NOMBRE_TRAMITE_BASE and not otra.name.startswith("~$"):
                TipoTramite.crear(otra.stem, otra)
