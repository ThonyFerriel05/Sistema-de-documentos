"""
configuracion.py
Último número de oficio usado antes de empezar a usar el sistema (RF16).
"""

from database import conectar


def obtener_ultimo_numero_previo(gestion, conexion=None):
    propia = conexion is None
    conexion = conexion or conectar()
    try:
        fila = conexion.execute(
            "SELECT ultimo_numero_previo FROM configuracion_gestion WHERE gestion = ?",
            (gestion,),
        ).fetchone()
        return fila["ultimo_numero_previo"] if fila else 0
    finally:
        if propia:
            conexion.close()


def definir_ultimo_numero_previo(gestion, numero):
    """
    La directora indica por qué número va en papel.
    Ejemplo: si pone 130, el próximo oficio del sistema será el 131.
    """
    numero = int(numero)
    if numero < 0:
        raise ValueError("El número no puede ser negativo.")
    with conectar() as conexion:
        mayor_en_sistema = conexion.execute(
            "SELECT COALESCE(MAX(codigo), 0) AS mayor FROM documento_expedido WHERE gestion = ?",
            (gestion,),
        ).fetchone()["mayor"]
        if numero < mayor_en_sistema:
            raise ValueError(
                f"Ya existe el oficio {mayor_en_sistema:02d}/{gestion} en el sistema. "
                f"El número no puede ser menor."
            )
        conexion.execute(
            """INSERT INTO configuracion_gestion (gestion, ultimo_numero_previo)
               VALUES (?, ?)
               ON CONFLICT(gestion) DO UPDATE SET ultimo_numero_previo = excluded.ultimo_numero_previo""",
            (gestion, numero),
        )
