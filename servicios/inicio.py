"""
inicio.py
Prepara todo la primera vez que se abre el sistema.
"""

from database import crear_tablas
from modelos.tipo_tramite import CARPETA_PLANTILLAS, TipoTramite
from servicios.plantillas import crear_plantilla_base

NOMBRE_TRAMITE_BASE = "Oficio general"


def preparar_sistema():
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
