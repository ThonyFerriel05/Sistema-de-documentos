"""
tipo_tramite.py
Clase TipoTramite: cada trámite frecuente con su plantilla Word (RF13, RF14).
"""

import shutil
from pathlib import Path

from database import CARPETA_SISTEMA, conectar
from utilidades import nombre_archivo_seguro

CARPETA_PLANTILLAS = CARPETA_SISTEMA / "plantillas"


class TipoTramite:
    def __init__(self, nombre, ruta_plantilla, id_tipo=None):
        self.id_tipo = id_tipo
        self.nombre = nombre
        self.ruta_plantilla = ruta_plantilla  # relativa a la carpeta del sistema

    # ---------- métodos del diagrama ----------

    def obtener_plantilla(self):
        """Devuelve la ruta completa del Word de este trámite."""
        ruta = CARPETA_SISTEMA / self.ruta_plantilla
        if not ruta.exists():
            raise FileNotFoundError(
                f"No se encontró la plantilla del trámite '{self.nombre}':\n{ruta}"
            )
        return ruta

    def reemplazar_plantilla(self, ruta_nueva):
        """Cambia el Word del trámite por otro que elija la directora."""
        self.ruta_plantilla = self._copiar_plantilla(ruta_nueva, self.nombre)
        with conectar() as conexion:
            conexion.execute(
                "UPDATE tipo_tramite SET ruta_plantilla = ? WHERE id_tipo = ?",
                (self.ruta_plantilla, self.id_tipo),
            )

    # ---------- guardar y consultar ----------

    def registrar(self):
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El trámite necesita un nombre.")
        with conectar() as conexion:
            existe = conexion.execute(
                "SELECT 1 FROM tipo_tramite WHERE nombre = ?", (self.nombre.strip(),)
            ).fetchone()
            if existe:
                raise ValueError(f"Ya existe un trámite llamado '{self.nombre}'.")
            cursor = conexion.execute(
                "INSERT INTO tipo_tramite (nombre, ruta_plantilla) VALUES (?, ?)",
                (self.nombre.strip(), self.ruta_plantilla),
            )
            self.id_tipo = cursor.lastrowid
        return self

    @classmethod
    def crear(cls, nombre, ruta_word_origen):
        """Registra un trámite nuevo copiando su Word a la carpeta de plantillas."""
        ruta = cls._copiar_plantilla(ruta_word_origen, nombre)
        return cls(nombre, ruta).registrar()

    @staticmethod
    def _copiar_plantilla(ruta_origen, nombre):
        origen = Path(ruta_origen)
        if origen.suffix.lower() != ".docx":
            raise ValueError("La plantilla debe ser un archivo de Word (.docx).")
        if not origen.exists():
            raise FileNotFoundError(f"No se encontró el archivo:\n{origen}")
        CARPETA_PLANTILLAS.mkdir(parents=True, exist_ok=True)
        destino = CARPETA_PLANTILLAS / f"{nombre_archivo_seguro(nombre)}.docx"
        if origen.resolve() != destino.resolve():
            shutil.copy2(origen, destino)
        return destino.relative_to(CARPETA_SISTEMA).as_posix()

    @classmethod
    def obtener(cls, id_tipo):
        with conectar() as conexion:
            fila = conexion.execute(
                "SELECT * FROM tipo_tramite WHERE id_tipo = ?", (id_tipo,)
            ).fetchone()
        if not fila:
            raise ValueError("No se encontró el trámite.")
        return cls(fila["nombre"], fila["ruta_plantilla"], fila["id_tipo"])

    @classmethod
    def listar(cls):
        with conectar() as conexion:
            filas = conexion.execute("SELECT * FROM tipo_tramite ORDER BY nombre").fetchall()
        return [cls(f["nombre"], f["ruta_plantilla"], f["id_tipo"]) for f in filas]
