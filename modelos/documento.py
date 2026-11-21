"""
documento.py
Clase abstracta Documento: lo que tienen en común expedidos y recibidos.
"""

import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from database import CARPETA_SISTEMA
from utilidades import abrir_con_programa, nombre_archivo_seguro

CARPETA_ARCHIVOS = CARPETA_SISTEMA / "archivos"


class Documento(ABC):
    """Nunca se crea un Documento 'a secas': siempre es expedido o recibido."""

    def __init__(self, asunto, archivo_escaneado=None):
        self.asunto = asunto
        # Se guarda la ruta relativa a la carpeta del sistema,
        # así la copia de seguridad funciona en cualquier computadora.
        self.archivo_escaneado = archivo_escaneado

    def abrir_archivo(self):
        """Abre el archivo escaneado (RF11)."""
        if not self.archivo_escaneado:
            raise ValueError("Este documento todavía no tiene un archivo escaneado.")
        abrir_con_programa(CARPETA_SISTEMA / self.archivo_escaneado)

    @staticmethod
    def copiar_escaneado(ruta_origen, subcarpeta, nombre_base):
        """
        Copia el escaneado que eligió la directora dentro de la carpeta
        del sistema (RNF04) y devuelve la ruta relativa.
        """
        origen = Path(ruta_origen)
        if not origen.exists():
            raise FileNotFoundError(f"No se encontró el archivo:\n{origen}")
        destino_carpeta = CARPETA_ARCHIVOS / subcarpeta
        destino_carpeta.mkdir(parents=True, exist_ok=True)

        nombre = nombre_archivo_seguro(nombre_base) + origen.suffix.lower()
        destino = destino_carpeta / nombre
        contador = 2
        while destino.exists():  # no pisar un archivo que ya existe
            destino = destino_carpeta / f"{nombre_archivo_seguro(nombre_base)} ({contador}){origen.suffix.lower()}"
            contador += 1

        shutil.copy2(origen, destino)
        return destino.relative_to(CARPETA_SISTEMA).as_posix()

    @abstractmethod
    def registrar(self):
        """Cada tipo de documento se guarda en su propia tabla."""
