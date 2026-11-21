"""
database.py
Crea y conecta la base de datos del sistema (SQLite).
Las tablas siguen el diagrama entidad-relación del diseño.
"""

import sqlite3
import sys
from pathlib import Path

# La base de datos es un solo archivo dentro de la carpeta del sistema.
# Si el programa está convertido en .exe, la carpeta es la del .exe.
if getattr(sys, "frozen", False):
    CARPETA_SISTEMA = Path(sys.executable).resolve().parent
else:
    CARPETA_SISTEMA = Path(__file__).resolve().parent
RUTA_BD = CARPETA_SISTEMA / "direccion.db"


class Conexion(sqlite3.Connection):
    """Conexión que, al salir de un 'with', guarda los cambios y se cierra sola."""

    def __exit__(self, tipo, valor, traza):
        resultado = super().__exit__(tipo, valor, traza)  # guarda o deshace
        self.close()
        return resultado


def conectar():
    """Abre una conexión con la base de datos."""
    conexion = sqlite3.connect(RUTA_BD, factory=Conexion)
    # SQLite no revisa las claves foráneas si no se le pide.
    conexion.execute("PRAGMA foreign_keys = ON")
    # Permite leer las columnas por su nombre: fila["codigo"]
    conexion.row_factory = sqlite3.Row
    return conexion


def _columnas(conexion, tabla):
    return [fila[1] for fila in conexion.execute(f"PRAGMA table_info({tabla})")]


def _apartar_tablas_viejas(conexion):
    """
    Si la base de datos es de la versión del 16 de noviembre (sin las columnas
    nuevas), renombra las tablas viejas para crear las nuevas y pasar los datos.
    Devuelve los nombres de las tablas que hay que migrar.
    """
    cambios = {
        "documento_expedido": "requiere_respuesta",
        "documento_recibido": "nro_registro",
        "acta": "nro_registro",
    }
    viejas = []
    for tabla, columna_nueva in cambios.items():
        columnas = _columnas(conexion, tabla)
        if columnas and columna_nueva not in columnas:
            conexion.execute(f"ALTER TABLE {tabla} RENAME TO {tabla}_v1")
            viejas.append(tabla)
    if "acta" in viejas:
        conexion.execute("DROP INDEX IF EXISTS idx_acta_carnet")
    return viejas


def _pasar_datos(conexion, viejas):
    """Copia los datos de las tablas viejas a las nuevas y borra las viejas."""
    if "documento_expedido" in viejas:
        conexion.execute(
            """INSERT INTO documento_expedido
               (id_expedido, codigo, gestion, fecha_envio, destinatario_nombre,
                destinatario_cargo, via_nombre, via_cargo, asunto, id_tipo,
                archivo_escaneado, requiere_respuesta, estado, nro_resolucion,
                fecha_resolucion, id_original)
               SELECT id_expedido, codigo, gestion, fecha_envio, destinatario_nombre,
                      destinatario_cargo, via_nombre, via_cargo, asunto, id_tipo,
                      archivo_escaneado, 1, estado, nro_resolucion, fecha_resolucion,
                      id_original
               FROM documento_expedido_v1"""
        )
    if "documento_recibido" in viejas:
        # Numera los que ya existían, en orden de llegada, dentro de cada gestión.
        conexion.execute(
            """INSERT INTO documento_recibido
               (id_recibido, nro_registro, gestion, categoria, nro_oficio,
                fecha_hora_recepcion, remitente, asunto, archivo_escaneado,
                requiere_respuesta, estado)
               SELECT id_recibido,
                      ROW_NUMBER() OVER (PARTITION BY substr(fecha_hora_recepcion, 1, 4)
                                         ORDER BY fecha_hora_recepcion, id_recibido),
                      CAST(substr(fecha_hora_recepcion, 1, 4) AS INTEGER), 'Otro',
                      nro_oficio, fecha_hora_recepcion, remitente, asunto,
                      archivo_escaneado, requiere_respuesta, estado
               FROM documento_recibido_v1"""
        )
    if "acta" in viejas:
        # Las actas viejas no tienen fecha: se toman como de la gestión actual.
        conexion.execute(
            """INSERT INTO acta
               (id_acta, nro_registro, gestion, nro_acta, codigo, carnet, nota,
                modalidad, archivo_escaneado)
               SELECT id_acta, ROW_NUMBER() OVER (ORDER BY id_acta),
                      CAST(strftime('%Y', 'now', 'localtime') AS INTEGER),
                      nro_acta, codigo, carnet, nota, modalidad, archivo_escaneado
               FROM acta_v1"""
        )
    for tabla in viejas:
        conexion.execute(f"DROP TABLE {tabla}_v1")


def crear_tablas():
    """Crea las tablas si todavía no existen (y actualiza una base vieja)."""
    with conectar() as conexion:
        # Mientras se reacomodan las tablas no se revisan las claves foráneas.
        conexion.execute("PRAGMA foreign_keys = OFF")
        viejas = _apartar_tablas_viejas(conexion)
        conexion.executescript(
            """
            -- Cada trámite frecuente con su plantilla Word (RF13, RF14)
            CREATE TABLE IF NOT EXISTS tipo_tramite (
                id_tipo         INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre          TEXT NOT NULL UNIQUE,
                ruta_plantilla  TEXT NOT NULL
            );

            -- Documentos que salen de la dirección (RF01, RF02, RF03)
            CREATE TABLE IF NOT EXISTS documento_expedido (
                id_expedido          INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo               INTEGER NOT NULL,
                gestion              INTEGER NOT NULL,
                fecha_envio          TEXT NOT NULL,
                destinatario_nombre  TEXT NOT NULL,
                destinatario_cargo   TEXT NOT NULL,
                via_nombre           TEXT,
                via_cargo            TEXT,
                asunto               TEXT NOT NULL,
                id_tipo              INTEGER NOT NULL REFERENCES tipo_tramite(id_tipo),
                archivo_escaneado    TEXT,
                -- Si no requiere respuesta, queda 'completado' desde que se registra
                requiere_respuesta   INTEGER NOT NULL DEFAULT 1
                                     CHECK (requiere_respuesta IN (0, 1)),
                estado               TEXT NOT NULL DEFAULT 'esperando'
                                     CHECK (estado IN ('esperando', 'aprobado', 'rechazado',
                                                       'completado')),
                nro_resolucion       TEXT,
                fecha_resolucion     TEXT,
                id_original          INTEGER REFERENCES documento_expedido(id_expedido),
                -- El mismo número no se repite dentro de una gestión
                UNIQUE (codigo, gestion)
            );

            -- Documentos que llegan a la dirección (RF04, RF05, RF17, RF18)
            CREATE TABLE IF NOT EXISTS documento_recibido (
                id_recibido           INTEGER PRIMARY KEY AUTOINCREMENT,
                -- Número interno de la dirección: vuelve a 1 cada gestión (RF18)
                nro_registro          INTEGER NOT NULL,
                gestion               INTEGER NOT NULL,
                categoria             TEXT NOT NULL DEFAULT 'Otro',
                nro_oficio            TEXT NOT NULL,
                fecha_hora_recepcion  TEXT NOT NULL,
                remitente             TEXT NOT NULL,
                asunto                TEXT NOT NULL,
                archivo_escaneado     TEXT,
                requiere_respuesta    INTEGER NOT NULL CHECK (requiere_respuesta IN (0, 1)),
                estado                TEXT NOT NULL DEFAULT 'pendiente'
                                      CHECK (estado IN ('pendiente', 'en curso', 'completado')),
                UNIQUE (nro_registro, gestion)
            );

            -- Actas de graduación (RF06, RF07, RF08, RF18, RF19)
            CREATE TABLE IF NOT EXISTS acta (
                id_acta            INTEGER PRIMARY KEY AUTOINCREMENT,
                -- Número interno de la dirección: vuelve a 1 cada gestión (RF18)
                nro_registro       INTEGER NOT NULL,
                gestion            INTEGER NOT NULL,
                nro_acta           TEXT NOT NULL UNIQUE,
                codigo             TEXT NOT NULL UNIQUE,
                carnet             TEXT NOT NULL,
                nota               INTEGER NOT NULL CHECK (nota BETWEEN 0 AND 100),
                modalidad          TEXT NOT NULL,
                archivo_escaneado  TEXT,
                UNIQUE (nro_registro, gestion)
            );

            -- Último número usado al empezar a usar el sistema (RF16)
            CREATE TABLE IF NOT EXISTS configuracion_gestion (
                gestion              INTEGER PRIMARY KEY,
                ultimo_numero_previo INTEGER NOT NULL DEFAULT 0
            );

            -- Para que buscar por carnet sea rápido (RF08)
            CREATE INDEX IF NOT EXISTS idx_acta_carnet ON acta(carnet);
            """
        )
        if viejas:
            conexion.execute("BEGIN")
            _pasar_datos(conexion, viejas)
        conexion.commit()
        conexion.execute("PRAGMA foreign_keys = ON")


if __name__ == "__main__":
    crear_tablas()
    print(f"Base de datos lista en: {RUTA_BD}")
